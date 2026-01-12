from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path
from typing import List, Tuple

from src.llm_analyze import SYSTEM_PROMPT, _call_with_retry
from src.ops.ops_context import create_ops_context
from src.security import validate_output


def load_prompts(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"Prompt corpus not found: {path}")
    prompts: List[str] = []
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    obj = json.loads(stripped)
                    if isinstance(obj, dict) and "prompt" in obj:
                        prompts.append(str(obj["prompt"]))
                    else:
                        prompts.append(str(obj))
                except json.JSONDecodeError:
                    prompts.append(stripped)
    else:
        prompts = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return prompts


def run_attempt(prompt: str, model: str, provider: str, ops) -> Tuple[bool, str]:
    """
    Returns (guardrail_holds, detail)
    guardrail_holds == True means validate_output passed (no jailbreak).
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    result = _call_with_retry(messages, model=model, provider=provider, ops=ops)
    # We treat policy validation failure as a jailbreak success.
    result_json = json.dumps(result, ensure_ascii=False)
    valid, policy_error = validate_output(result_json)
    if valid:
        return True, ""
    return False, policy_error or "Policy violation detected"


def write_summary(run_dir: Path, attempts: int, successes: int, details: List[dict]) -> Path:
    summary = {
        "attempts": attempts,
        "jailbreak_successes": successes,
        "details": details,
    }
    out_path = run_dir / "jailbreak_results.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Jailbreak harness replay")
    parser.add_argument("--prompts", required=True, help="Path to jailbreak prompts (jsonl or txt)")
    parser.add_argument("--model", default="gemini-flash-latest", help="Model to use")
    parser.add_argument("--provider", choices=["openai", "gemini"], default="gemini", help="LLM provider")
    parser.add_argument("--limit", type=int, help="Optional limit on number of prompts")
    args = parser.parse_args()

    prompts_path = Path(args.prompts)
    prompts = load_prompts(prompts_path)
    if args.limit:
        prompts = prompts[: args.limit]

    run_id = str(uuid.uuid4())
    ops = create_ops_context(run_id)
    ops.set_source_type("jailbreak")
    ops.log_run_start(
        {
            "prompts_file": str(prompts_path),
            "model": args.model,
            "provider": args.provider,
            "prompt_count": len(prompts),
        }
    )

    ops.stage_start("jailbreak_harness", records_in=len(prompts))

    attempts = 0
    successes = 0
    details: List[dict] = []

    for idx, prompt in enumerate(prompts, start=1):
        attempts += 1
        guardrail_holds, reason = run_attempt(prompt, args.model, args.provider, ops)
        if not guardrail_holds:
            successes += 1
        details.append(
            {
                "index": idx,
                "prompt_excerpt": prompt[:200],
                "guardrail_holds": guardrail_holds,
                "reason": reason,
            }
        )

    ops.metrics.record_jailbreak_results(attempts, successes)
    ops.stage_end(
        "jailbreak_harness",
        ok=True,
        records_in=len(prompts),
        records_out=len(prompts),
        extra_fields={
            "jailbreak_attempts": attempts,
            "jailbreak_successes": successes,
        },
    )

    results_path = write_summary(ops.run_dir, attempts, successes, details)
    ops.finalize(ok=True)

    print(f"Jailbreak harness complete. Attempts={attempts}, successes={successes}")
    print(f"Results written to {results_path}")
    print(f"Ops artifacts written to {ops.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
