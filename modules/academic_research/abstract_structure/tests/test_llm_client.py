"""llm_client 测试：空响应循环内重试逻辑（mock _post，不发起真实 API 调用）。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import llm_client as lc  # noqa: E402


@pytest.fixture()
def client(tmp_path: Path, monkeypatch) -> lc.DeepSeekClient:
    env = tmp_path / ".env"
    env.write_text("DEEPSEEK_API_KEY=dummy-test-key\n", encoding="utf-8")
    monkeypatch.setattr(lc.time, "sleep", lambda _s: None)  # 不真实等待
    return lc.DeepSeekClient(model="deepseek-v4-flash", env_path=env,
                             budget=lc.BudgetGuard())


def _resp(content: str, total: int = 100, reasoning: int = 0) -> dict:
    return {
        "content": content,
        "usage": {"prompt_tokens": 50, "completion_tokens": 50,
                  "total_tokens": total,
                  "completion_tokens_details": {"reasoning_tokens": reasoning}},
        "model_returned": "deepseek-v4-flash",
    }


def test_empty_response_retried_then_success(client, monkeypatch):
    """空响应在循环内重试；第 3 次返回正常内容即成功。"""
    calls = []

    def fake_post(body):
        calls.append(1)
        if len(calls) < 3:
            return _resp("", reasoning=32000)
        return _resp('{"ok": true}')

    monkeypatch.setattr(client, "_post", fake_post)
    out = client.chat("sys", {"x": 1}, "h", "pysbd 0.3.4")
    assert out["content"] == '{"ok": true}'
    assert len(calls) == 3
    # 重试计入预算：2 次空响应 + 1 次成功
    assert client.budget.n_requests == 3


def test_empty_response_persistent_raises_non_transient(client, monkeypatch):
    """重试 MAX_TRANSIENT_RETRIES 次后仍为空 → 非 transient LLMCallError。"""
    monkeypatch.setattr(client, "_post",
                        lambda body: _resp("", reasoning=32000))
    with pytest.raises(lc.LLMCallError) as ei:
        client.chat("sys", {"x": 1}, "h", "pysbd 0.3.4")
    assert ei.value.transient is False
    assert "空响应" in str(ei.value)
    assert client.budget.n_requests == 1 + lc.MAX_TRANSIENT_RETRIES


def test_whitespace_only_response_treated_as_empty(client, monkeypatch):
    monkeypatch.setattr(client, "_post", lambda body: _resp("   \n  "))
    with pytest.raises(lc.LLMCallError):
        client.chat("sys", {"x": 1}, "h", "pysbd 0.3.4")


def test_transient_http_error_still_retried(client, monkeypatch):
    calls = []

    def fake_post(body):
        calls.append(1)
        if len(calls) == 1:
            raise lc.LLMCallError("暂时性 HTTP 429", transient=True)
        return _resp('{"ok": 1}')

    monkeypatch.setattr(client, "_post", fake_post)
    out = client.chat("sys", {"x": 1}, "h", "pysbd 0.3.4")
    assert out["content"] == '{"ok": 1}'
    assert len(calls) == 2


def test_empty_response_escalates_max_tokens_when_reasoning_exhausted(client, monkeypatch):
    """reasoning_tokens 达到当前 max_tokens（耗尽）→ 重试时 max_tokens 翻倍并记录。"""
    bodies = []

    def fake_post(body):
        bodies.append(dict(body))
        if len(bodies) == 1:
            return _resp("", reasoning=4096)
        return _resp('{"ok": true}')

    monkeypatch.setattr(client, "_post", fake_post)
    out = client.chat("sys", {"x": 1}, "h", "pysbd 0.3.4", max_tokens=4096)
    assert bodies[0]["max_tokens"] == 4096
    assert bodies[1]["max_tokens"] == 8192
    assert out["max_tokens_escalated"] == {"initial": 4096, "final": 8192}


def test_empty_response_no_escalation_below_cap_or_without_exhaustion(client, monkeypatch):
    """reasoning 未耗尽则不升级；已在上限时 reasoning 再大也不超限升级。"""
    bodies = []

    def fake_post(body):
        bodies.append(dict(body))
        if len(bodies) == 1:
            return _resp("", reasoning=100)  # 远未耗尽，可能是其他原因
        return _resp('{"ok": true}')

    monkeypatch.setattr(client, "_post", fake_post)
    out = client.chat("sys", {"x": 1}, "h", "pysbd 0.3.4", max_tokens=4096)
    assert bodies[1]["max_tokens"] == 4096
    assert "max_tokens_escalated" not in out

    bodies.clear()

    def fake_post2(body):
        bodies.append(dict(body))
        if len(bodies) == 1:
            return _resp("", reasoning=lc.EMPTY_RESPONSE_MAX_TOKENS_CAP)
        return _resp('{"ok": true}')

    monkeypatch.setattr(client, "_post", fake_post2)
    client.chat("sys", {"x": 1}, "h", "pysbd 0.3.4",
                max_tokens=lc.EMPTY_RESPONSE_MAX_TOKENS_CAP)
    assert bodies[1]["max_tokens"] == lc.EMPTY_RESPONSE_MAX_TOKENS_CAP
