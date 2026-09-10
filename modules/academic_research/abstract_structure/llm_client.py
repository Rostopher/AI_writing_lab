"""DeepSeek（OpenAI-compatible）chat completions 客户端。

- base_url 默认 https://api.deepseek.com；模型 deepseek-v4-flash / deepseek-v4-pro。
- API key：优先读环境变量 DEEPSEEK_API_KEY；否则经 python-dotenv 从 .env 文件读取
  （路径由环境变量 DEEPSEEK_ENV_FILE 或 DeepSeekClient(env_path=...) 指定）。
  任何日志、请求落盘、异常信息均不得包含 key。
- temperature=0；优先 response_format=json_object，不支持时记录并退回普通模式。
- 预算护栏：max_requests / max_total_tokens / max_cost_cny，超限即停（BudgetExceeded）。
- 计价 CNY/百万 token（来源 LLMClient/token_usage_tracker.py，核验日期 2026-09-08）：
  flash 输入 1.0 输出 2.0（缓存命中输入 0.02）；pro 输入 3.0 输出 6.0（缓存命中 0.025）。
- 缓存键 = 规范文本 hash + 切句版本 + system/user prompt hash + 模型 + 参数。
  请求存 requests/（不含认证头），原始响应存 responses/，不覆盖写。
- 重试：暂时性网络/限流（429/5xx/连接错误）最多额外 2 次；认证错误（401/403）不重试。
  空响应（推理模型 reasoning_tokens 耗尽 max_tokens）同样在循环内重试，重试计入预算；
  若 reasoning_tokens 达到当前 max_tokens，重试时 max_tokens 翻倍（上限 65536，
  缓存键按初始参数计算）；重试后仍为空则以非 transient LLMCallError 抛出
  （记 api_call 失败，不触发修复请求）。
  格式/契约失败的修复请求由 run_annotation 层实现（最多 1 次）。
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path

import requests
from dotenv import dotenv_values

DEFAULT_BASE_URL = "https://api.deepseek.com"
_env_file = os.environ.get("DEEPSEEK_ENV_FILE")
DEFAULT_ENV_PATH = Path(_env_file) if _env_file else None
ENV_KEY_NAME = "DEEPSEEK_API_KEY"
MODELS = ("deepseek-v4-flash", "deepseek-v4-pro")

# CNY / 百万 token；来源 LLMClient/token_usage_tracker.py
PRICE_VERIFIED_DATE = "2026-09-08"
PRICE_TABLE = {
    "deepseek-v4-flash": {"input": 1.0, "output": 2.0, "cache_hit_input": 0.02},
    "deepseek-v4-pro": {"input": 3.0, "output": 6.0, "cache_hit_input": 0.025},
}

MAX_TRANSIENT_RETRIES = 2  # 额外重试次数
RETRY_BACKOFF_SECONDS = (5.0, 20.0)
# 空响应且 reasoning_tokens 达到当前 max_tokens（推理耗尽）时，重试把 max_tokens
# 翻倍升级，上限 65536；缓存键始终按初始参数计算，升级不影响命中。
EMPTY_RESPONSE_MAX_TOKENS_CAP = 65536


class BudgetExceeded(RuntimeError):
    pass


class AuthenticationError(RuntimeError):
    pass


class LLMCallError(RuntimeError):
    """暂时性失败（可重试）或最终失败。transient 标记是否可重试。"""

    def __init__(self, message: str, transient: bool = True):
        super().__init__(message)
        self.transient = transient


class BudgetGuard:
    def __init__(self, max_requests: int | None = None,
                 max_total_tokens: int | None = None,
                 max_cost_cny: float | None = None):
        self.max_requests = max_requests
        self.max_total_tokens = max_total_tokens
        self.max_cost_cny = max_cost_cny
        self.n_requests = 0
        self.total_tokens = 0
        self.total_cost_cny = 0.0
        self._lock = threading.Lock()

    def check_before_call(self) -> None:
        with self._lock:
            if self.max_requests is not None and self.n_requests >= self.max_requests:
                raise BudgetExceeded(
                    f"已达 max_requests={self.max_requests}（已用 {self.n_requests}）")

    def record(self, n_tokens: int, cost_cny: float) -> None:
        with self._lock:
            self.n_requests += 1
            self.total_tokens += n_tokens
            self.total_cost_cny += cost_cny
            if self.max_total_tokens is not None and self.total_tokens > self.max_total_tokens:
                raise BudgetExceeded(
                    f"已超 max_total_tokens={self.max_total_tokens}（已用 {self.total_tokens}）")
            if self.max_cost_cny is not None and self.total_cost_cny > self.max_cost_cny:
                raise BudgetExceeded(
                    f"已超 max_cost_cny={self.max_cost_cny}（已用 {self.total_cost_cny:.4f}）")


def compute_cost_cny(model: str, usage: dict) -> float | None:
    """按 PRICE_TABLE 计价；用量缺失或模型未知返回 None（费用记 unknown，不记 0）。"""
    price = PRICE_TABLE.get(model)
    if price is None:
        return None
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    if prompt is None or completion is None:
        return None
    hit = usage.get("prompt_cache_hit_tokens")
    if isinstance(hit, int) and 0 <= hit <= prompt:
        miss = prompt - hit
        return (miss * price["input"] + hit * price["cache_hit_input"]
                + completion * price["output"]) / 1_000_000
    return (prompt * price["input"] + completion * price["output"]) / 1_000_000


def load_api_key(env_path: Path | None = DEFAULT_ENV_PATH) -> str:
    key = os.environ.get(ENV_KEY_NAME)
    if key:
        return key
    if env_path is None:
        raise AuthenticationError(
            f"未配置 {ENV_KEY_NAME}：请设置环境变量 {ENV_KEY_NAME}，"
            f"或用 DEEPSEEK_ENV_FILE 指定含该变量的 .env 文件")
    values = dotenv_values(env_path)
    key = values.get(ENV_KEY_NAME)
    if not key:
        raise AuthenticationError(f"未在 {env_path} 找到 {ENV_KEY_NAME}")
    return key


def make_cache_key(norm_text_hash: str, splitter_version: str,
                   system_prompt: str, user_payload: dict,
                   model: str, params: dict) -> str:
    h = hashlib.sha256()
    h.update(norm_text_hash.encode())
    h.update(splitter_version.encode())
    h.update(hashlib.sha256(system_prompt.encode()).hexdigest().encode())
    h.update(hashlib.sha256(
        json.dumps(user_payload, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest().encode())
    h.update(model.encode())
    h.update(json.dumps(params, sort_keys=True).encode())
    return h.hexdigest()


class DeepSeekClient:
    def __init__(self, model: str = "deepseek-v4-flash",
                 base_url: str = DEFAULT_BASE_URL,
                 env_path: Path | None = DEFAULT_ENV_PATH,
                 budget: BudgetGuard | None = None,
                 cache_dir: Path | None = None,
                 timeout_seconds: float = 120.0):
        if model not in MODELS:
            raise ValueError(f"未知模型 {model!r}，允许: {MODELS}")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._api_key = load_api_key(env_path)
        self.budget = budget or BudgetGuard()
        self.cache_dir = cache_dir
        self.timeout = timeout_seconds
        self.json_object_supported: bool | None = None  # None=未探测
        if cache_dir:
            (cache_dir / "requests").mkdir(parents=True, exist_ok=True)
            (cache_dir / "responses").mkdir(parents=True, exist_ok=True)

    def _cache_paths(self, key: str) -> tuple[Path, Path]:
        assert self.cache_dir is not None
        return (self.cache_dir / "requests" / f"{key}.json",
                self.cache_dir / "responses" / f"{key}.json")

    def chat(self, system_prompt: str, user_payload: dict,
             norm_text_hash: str, splitter_version: str,
             max_tokens: int = 32768) -> dict:
        """调用一次（含缓存与重试）。返回 {content, usage, cost_cny, model_returned,
        cache_key, cached, json_object_mode}。失败抛 LLMCallError/AuthenticationError。"""
        params = {"temperature": 0, "max_tokens": max_tokens}
        cache_key = make_cache_key(norm_text_hash, splitter_version, system_prompt,
                                   user_payload, self.model, params)
        if self.cache_dir:
            req_path, resp_path = self._cache_paths(cache_key)
            if resp_path.exists():
                cached = json.loads(resp_path.read_text(encoding="utf-8"))
                cached["cached"] = True
                return cached

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ]
        use_json_object = self.json_object_supported is not False
        body: dict = {"model": self.model, "messages": messages, **params}
        if use_json_object:
            body["response_format"] = {"type": "json_object"}

        self.budget.check_before_call()
        last_err: LLMCallError | None = None
        result: dict | None = None
        current_max_tokens = max_tokens
        for attempt in range(1 + MAX_TRANSIENT_RETRIES):
            try:
                result = self._post(body)
            except LLMCallError as e:
                last_err = e
                # response_format 不支持：记录并退回普通模式（本次调用内直接重发）
                if use_json_object and e.transient is False and "response_format" in str(e):
                    self.json_object_supported = False
                    body.pop("response_format", None)
                    use_json_object = False
                    continue
                if not e.transient or attempt >= MAX_TRANSIENT_RETRIES:
                    raise
                time.sleep(RETRY_BACKOFF_SECONDS[min(attempt, len(RETRY_BACKOFF_SECONDS) - 1)])
                continue
            # 推理模型可能把 max_tokens 全部用于 reasoning 导致 content 为空：
            # 在循环内重试（重试计入预算）；若 reasoning_tokens 达到当前 max_tokens
            # 说明是耗尽所致，重试时把 max_tokens 翻倍（上限
            # EMPTY_RESPONSE_MAX_TOKENS_CAP）。仍为空则以非 transient 错误抛出，
            # 由 run_annotation 记入 failures.jsonl 的 api_call 阶段，不触发修复请求。
            if not (result["content"] or "").strip():
                usage0 = result["usage"]
                reasoning = (usage0.get("completion_tokens_details") or {}).get(
                    "reasoning_tokens")
                self.budget.record(int(usage0.get("total_tokens") or 0),
                                   compute_cost_cny(self.model, usage0) or 0.0)
                last_err = LLMCallError(
                    f"空响应（reasoning_tokens={reasoning} 可能耗尽 max_tokens）",
                    transient=True)
                result = None
                if attempt >= MAX_TRANSIENT_RETRIES:
                    raise LLMCallError(
                        f"空响应（reasoning_tokens={reasoning} 可能耗尽 max_tokens），"
                        f"重试 {MAX_TRANSIENT_RETRIES} 次后仍为空", transient=False)
                if (isinstance(reasoning, int) and reasoning >= current_max_tokens
                        and current_max_tokens < EMPTY_RESPONSE_MAX_TOKENS_CAP):
                    current_max_tokens = min(current_max_tokens * 2,
                                             EMPTY_RESPONSE_MAX_TOKENS_CAP)
                    body["max_tokens"] = current_max_tokens
                time.sleep(RETRY_BACKOFF_SECONDS[min(attempt, len(RETRY_BACKOFF_SECONDS) - 1)])
                continue
            break
        if result is None:
            raise last_err or LLMCallError("未知失败", transient=False)

        usage = result["usage"]
        n_tokens = int(usage.get("total_tokens") or 0)
        cost = compute_cost_cny(self.model, usage)
        out = {
            "content": result["content"],
            "usage": usage,
            "cost_cny": cost,
            "model_requested": self.model,
            "model_returned": result.get("model_returned"),
            "cache_key": cache_key,
            "cached": False,
            "json_object_mode": use_json_object,
            "called_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if current_max_tokens != max_tokens:
            out["max_tokens_escalated"] = {"initial": max_tokens,
                                           "final": current_max_tokens}
        self.budget.record(n_tokens, cost or 0.0)
        if self.cache_dir:
            req_path, resp_path = self._cache_paths(cache_key)
            # 请求落盘不含认证头
            req_path.write_text(json.dumps(
                {"url": f"{self.base_url}/chat/completions", "body": body},
                ensure_ascii=False, indent=2), encoding="utf-8")
            resp_path.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
        return out

    def _post(self, body: dict) -> dict:
        headers = {"Authorization": f"Bearer {self._api_key}",
                   "Content-Type": "application/json"}
        try:
            resp = requests.post(f"{self.base_url}/chat/completions",
                                 json=body, headers=headers, timeout=self.timeout)
        except requests.RequestException as e:
            raise LLMCallError(f"网络错误: {type(e).__name__}", transient=True) from e
        if resp.status_code in (401, 403):
            raise AuthenticationError(f"认证失败 HTTP {resp.status_code}（不重试）")
        if resp.status_code in (408, 409, 429) or resp.status_code >= 500:
            raise LLMCallError(f"暂时性 HTTP {resp.status_code}", transient=True)
        if resp.status_code == 400 and "response_format" in resp.text:
            raise LLMCallError(
                "API 不支持 response_format json_object，退回普通模式", transient=False)
        if resp.status_code != 200:
            raise LLMCallError(f"HTTP {resp.status_code}: {resp.text[:200]}",
                               transient=False)
        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise LLMCallError(f"响应结构异常: {e}", transient=False) from e
        return {
            "content": content,
            "usage": data.get("usage") or {},
            "model_returned": data.get("model"),
        }
