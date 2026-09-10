"""批量标注执行：读 sample manifest + prompt 版本文件，程序构造 USER_PAYLOAD，
调用 LLM、校验、落盘 annotations.jsonl + failures.jsonl。

用法：
  # dry-run（不调用，仅估算 token 与费用）
  python run_annotation.py --sample <sample.jsonl> --task annotation --dry-run
  # 真实调用（需预算护栏，本研究阶段不预先调用付费模型）
  python run_annotation.py --sample <sample.jsonl> --task annotation \
      --model deepseek-v4-flash --max-requests 100 --max-cost-cny 50

sample manifest：JSONL，每行 {"article_id": ...}；article_id 须在 corpus_manifest 中
且 availability=available、selected=true。
USER_PAYLOAD 由程序构造为 dict 再 json.dumps，不作字符串模板拼接。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_abstracts import OUTPUT_ROOT  # noqa: E402
from llm_client import (  # noqa: E402
    MODELS,
    PRICE_TABLE,
    PRICE_VERIFIED_DATE,
    AuthenticationError,
    BudgetExceeded,
    BudgetGuard,
    DeepSeekClient,
    LLMCallError,
)
from textnorm import SENTENCE_SPLITTER  # noqa: E402
from validate_output import (  # noqa: E402
    SCHEMA_VERSION_ANNOTATION,
    SCHEMA_VERSION_RULES,
    validate_annotation_output,
    validate_rules_output,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPT_FILES = {
    "annotation": REPO_ROOT / "ideas" / "abstract_structure_annotation_prompt.md",
    "rules": REPO_ROOT / "ideas" / "abstract_rules_audit_prompt.md",
}
SCHEMA_VERSIONS = {
    "annotation": SCHEMA_VERSION_ANNOTATION,
    "rules": SCHEMA_VERSION_RULES,
}
VALIDATORS = {
    "annotation": validate_annotation_output,
    "rules": validate_rules_output,
}
CHARS_PER_TOKEN_EST = 4  # 英文文本粗估，仅用于 dry-run 估算


def load_system_prompt(prompt_file: Path) -> str:
    """从 prompt 版本文件中提取 `## SYSTEM_PROMPT` 后的 ```text 代码块。"""
    text = prompt_file.read_text(encoding="utf-8")
    m = re.search(r"##\s+SYSTEM_PROMPT\s*\n+```text\n(.*?)```", text, re.DOTALL)
    if not m:
        raise ValueError(f"无法在 {prompt_file} 中定位 SYSTEM_PROMPT 代码块")
    return m.group(1).strip("\n")


def load_prompt_version(prompt_file: Path) -> str:
    """从 prompt 版本文件头部 `> 版本：0.3` 行解析版本号（如 'v0.3'）。

    供校验器做版本化语义检查（如 v0.3 起 how_aspects 禁 mechanism）。"""
    text = prompt_file.read_text(encoding="utf-8")
    m = re.search(r"版本：\s*v?(\d+\.\d+)", text)
    if not m:
        raise ValueError(f"无法在 {prompt_file} 头部定位版本号（期望形如 '> 版本：0.3'）")
    return f"v{m.group(1)}"


def load_corpus(corpus_path: Path) -> dict[str, dict]:
    corpus: dict[str, dict] = {}
    with open(corpus_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            corpus[rec["article_id"]] = rec
    return corpus


def load_sample_ids(sample_path: Path) -> list[str]:
    ids: list[str] = []
    with open(sample_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("{"):
                ids.append(json.loads(line)["article_id"])
            else:
                ids.append(line)
    return ids


def build_user_payload(task: str, article_id: str, sentences: list[dict]) -> dict:
    """程序构造 USER_PAYLOAD（dict → JSON），只含契约字段。"""
    return {
        "schema_version": SCHEMA_VERSIONS[task],
        "article_id": article_id,
        "sentences": [{"sentence_id": s["sentence_id"], "text": s["text"]}
                      for s in sentences],
    }


def eligible_record(rec: dict) -> bool:
    return (rec.get("selected") is True and rec.get("included") is True
            and rec.get("availability") == "available"
            and rec.get("sentences"))


def dry_run(task: str, ids: list[str], corpus: dict[str, dict],
            system_prompt: str, model: str) -> None:
    price = PRICE_TABLE[model]
    total_in = total_out = 0
    skipped: list[str] = []
    for aid in ids:
        rec = corpus.get(aid)
        if rec is None or not eligible_record(rec):
            skipped.append(aid)
            continue
        payload = build_user_payload(task, aid, rec["sentences"])
        user_json = json.dumps(payload, ensure_ascii=False)
        total_in += (len(system_prompt) + len(user_json)) / CHARS_PER_TOKEN_EST
        # 输出粗估：每个句子的标注 JSON 约为输入句文本的 1.5 倍 + 固定开销
        total_out += len(user_json) * 1.5 / CHARS_PER_TOKEN_EST + 200
    n = len(ids) - len(skipped)
    est_in, est_out = int(total_in), int(total_out)
    est_cost = (est_in * price["input"] + est_out * price["output"]) / 1_000_000
    print(f"[dry-run] task={task} model={model} schema={SCHEMA_VERSIONS[task]}")
    print(f"[dry-run] 样本 {len(ids)} 篇，可标注 {n} 篇，跳过 {len(skipped)} 篇")
    for aid in skipped:
        print(f"[dry-run]   跳过 {aid}（不在 corpus 或不满足 selected/included/available）")
    print(f"[dry-run] 估算输入 {est_in:,} token，输出 {est_out:,} token，"
          f"费用约 ¥{est_cost:.4f}（{model}: 输入 ¥{price['input']}/M，输出 ¥{price['output']}/M，"
          f"计价核验 {PRICE_VERIFIED_DATE}）")
    if n:
        first = corpus[[a for a in ids if a not in skipped][0]]
        demo = build_user_payload(task, first["article_id"], first["sentences"])
        print("[dry-run] USER_PAYLOAD 示例（首篇，程序构造）：")
        print(json.dumps(demo, ensure_ascii=False, indent=2)[:1200])
    print("[dry-run] 未发起任何 API 调用。")


def run(task: str, ids: list[str], corpus: dict[str, dict], system_prompt: str,
        client: DeepSeekClient, run_dir: Path, prompt_version: str = "v0.1",
        concurrency: int = 1) -> dict:
    """批量执行。concurrency>1 时用线程池并发（调用是 I/O 密集）；
    输出行按完成顺序追加，不再与输入顺序一致。预算/认证错误置停止标记：
    进行中的调用继续，未开始的记 skipped（原因可溯），不再发起新调用。
    断点续跑：annotations.jsonl 中已有的 article_id 直接跳过（容忍被掐断时
    写入的残缺行），重复执行同一 run_dir 不会产生重复标注。"""
    ann_path = run_dir / "annotations.jsonl"
    fail_path = run_dir / "failures.jsonl"
    base_validator = VALIDATORS[task]
    if task == "annotation":
        validator = partial(base_validator, prompt_version=prompt_version)
    else:
        validator = base_validator
    done_ids: set[str] = set()
    if ann_path.exists():
        with open(ann_path, encoding="utf-8") as f:
            for line in f:
                try:
                    done_ids.add(json.loads(line)["article_id"])
                except (json.JSONDecodeError, KeyError):
                    continue  # 掐断造成的残缺行：忽略，对应文章会因未登记而重跑
    pending = [aid for aid in ids if aid not in done_ids]
    n_resumed = len(ids) - len(pending)
    stats = {"n_total": 0, "n_success_original": 0, "n_success_repaired": 0,
             "n_failed": 0, "n_skipped": 0, "n_resume_skipped": n_resumed}
    stop = threading.Event()
    write_lock = threading.Lock()

    def process_one(aid: str):
        """返回 (status, ann_record, fail_record)。"""
        if stop.is_set():
            return ("skipped", None,
                    {"article_id": aid, "stage": "stopped",
                     "error": "预算或认证中止后不再开始新任务"})
        rec = corpus.get(aid)
        if rec is None or not eligible_record(rec):
            return ("skipped", None,
                    {"article_id": aid, "stage": "eligibility",
                     "error": "不在 corpus 或不满足 selected/included/available"})
        payload = build_user_payload(task, aid, rec["sentences"])
        norm_hash = rec.get("abstract_norm_sha256") or ""
        try:
            resp = client.chat(system_prompt, payload, norm_hash, SENTENCE_SPLITTER)
        except (BudgetExceeded, AuthenticationError) as e:
            stop.set()
            return ("fatal", None,
                    {"article_id": aid, "stage": "api_call",
                     "error": f"{type(e).__name__}: {e}"})
        except LLMCallError as e:
            return ("failed", None,
                    {"article_id": aid, "stage": "api_call",
                     "error": f"{type(e).__name__}: {e}"})

        parse_err = None
        try:
            obj = json.loads(resp["content"])
        except json.JSONDecodeError as e:
            obj, parse_err = None, f"JSONDecodeError: {e}"
        vr = (validator(obj, aid, rec["sentences"]) if obj is not None else None)

        if vr is not None and vr.ok:
            return ("success_original",
                    {"article_id": aid, "task": task,
                     "model": resp["model_returned"],
                     "cache_key": resp["cache_key"],
                     "cost_cny": resp["cost_cny"],
                     "needs_review": vr.needs_review,
                     "output": obj}, None)

        # 契约失败：最多 1 次修复请求（只给原输入+原响应+校验错误，不加标签暗示）
        errors = [parse_err] if parse_err else vr.errors
        repair_payload = {
            "schema_version": payload["schema_version"],
            "article_id": aid,
            "sentences": payload["sentences"],
            "repair_request": {
                "previous_response": resp["content"][:20000],
                "validation_errors": errors,
                "instruction": ("Re-output the complete corrected JSON object only. "
                                "Fix the listed validation errors without changing "
                                "unaffected content."),
            },
        }
        try:
            resp2 = client.chat(system_prompt, repair_payload, norm_hash,
                                SENTENCE_SPLITTER)
            obj2 = json.loads(resp2["content"])
            vr2 = validator(obj2, aid, rec["sentences"])
        except (BudgetExceeded, AuthenticationError) as e:
            stop.set()
            return ("fatal", None,
                    {"article_id": aid, "stage": "repair_call",
                     "error": f"{type(e).__name__}: {e}",
                     "original_errors": errors})
        except (LLMCallError, json.JSONDecodeError) as e:
            return ("failed", None,
                    {"article_id": aid, "stage": "repair_call",
                     "error": f"{type(e).__name__}: {e}",
                     "original_errors": errors})
        if vr2.ok:
            return ("success_repaired",
                    {"article_id": aid, "task": task,
                     "model": resp2["model_returned"],
                     "cache_key": resp2["cache_key"],
                     "cost_cny": (resp["cost_cny"] or 0)
                     + (resp2["cost_cny"] or 0),
                     "repaired": True,
                     "needs_review": vr2.needs_review,
                     "output": obj2}, None)
        return ("failed", None,
                {"article_id": aid, "stage": "validation",
                 "original_errors": errors,
                 "repair_errors": vr2.errors,
                 "raw_response_cached": resp["cache_key"]})

    def apply(status: str, ann_rec: dict | None, fail_rec: dict | None) -> None:
        stats["n_total"] += 1
        if status == "success_original":
            stats["n_success_original"] += 1
        elif status == "success_repaired":
            stats["n_success_repaired"] += 1
        elif status == "skipped":
            stats["n_skipped"] += 1
        else:
            stats["n_failed"] += 1  # failed / fatal
        with write_lock:
            if ann_rec is not None:
                fa.write(json.dumps(ann_rec, ensure_ascii=False) + "\n")
            if fail_rec is not None:
                ff.write(json.dumps(fail_rec, ensure_ascii=False) + "\n")
        if status == "fatal":
            print(f"预算或认证中止: {fail_rec['error']}")

    with open(ann_path, "a", encoding="utf-8") as fa, \
            open(fail_path, "a", encoding="utf-8") as ff:
        if concurrency <= 1:
            for aid in pending:
                apply(*process_one(aid))
                if stop.is_set():
                    break
        else:
            with ThreadPoolExecutor(max_workers=concurrency) as ex:
                futures = [ex.submit(process_one, aid) for aid in pending]
                for fut in as_completed(futures):
                    apply(*fut.result())
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="摘要结构/规则批量标注")
    ap.add_argument("--sample", type=Path, required=True, help="sample manifest（article_id 列表）")
    ap.add_argument("--corpus", type=Path,
                    default=OUTPUT_ROOT / "run_20260908_a" / "corpus_manifest.jsonl")
    ap.add_argument("--task", choices=list(PROMPT_FILES), required=True)
    ap.add_argument("--prompt-file", type=Path, default=None,
                    help="prompt 版本文件（默认 ideas/ 下对应文件）")
    ap.add_argument("--model", choices=list(MODELS), default="deepseek-v4-flash")
    ap.add_argument("--run-dir", type=Path, default=None,
                    help="输出目录（默认 <corpus 所在目录>/annotation_<task>_<model>）")
    ap.add_argument("--dry-run", action="store_true", help="不调用 API，仅估算 token 与费用")
    ap.add_argument("--max-requests", type=int, default=None)
    ap.add_argument("--max-total-tokens", type=int, default=None)
    ap.add_argument("--max-cost-cny", type=float, default=None)
    ap.add_argument("--concurrency", type=int, default=1,
                    help="并发线程数（默认 1=串行；输出按完成顺序追加）")
    args = ap.parse_args(argv)

    prompt_file = args.prompt_file or PROMPT_FILES[args.task]
    system_prompt = load_system_prompt(prompt_file)
    prompt_version = load_prompt_version(prompt_file)
    corpus = load_corpus(args.corpus)
    ids = load_sample_ids(args.sample)

    if args.dry_run:
        dry_run(args.task, ids, corpus, system_prompt, args.model)
        return 0

    run_dir = args.run_dir or args.corpus.parent / f"annotation_{args.task}_{args.model}"
    run_dir.mkdir(parents=True, exist_ok=True)
    budget = BudgetGuard(max_requests=args.max_requests,
                         max_total_tokens=args.max_total_tokens,
                         max_cost_cny=args.max_cost_cny)
    client = DeepSeekClient(model=args.model, budget=budget, cache_dir=run_dir)
    started = datetime.now(timezone.utc)
    stats = run(args.task, ids, corpus, system_prompt, client, run_dir,
                prompt_version=prompt_version, concurrency=args.concurrency)
    print(json.dumps({"started_at": started.isoformat(timespec="seconds"),
                      "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                      "prompt_file": str(prompt_file),
                      "prompt_version": prompt_version,
                      "concurrency": args.concurrency,
                      **stats,
                      "budget": {"n_requests": budget.n_requests,
                                 "total_tokens": budget.total_tokens,
                                 "total_cost_cny": round(budget.total_cost_cny, 4)}},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
