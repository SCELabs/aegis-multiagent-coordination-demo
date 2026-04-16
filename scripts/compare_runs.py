from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def summarize_rows(rows):
    cases = len(rows)
    total_steps = sum(r["metrics"]["total_steps"] for r in rows)
    total_llm_calls = sum(r["metrics"]["total_llm_calls"] for r in rows)
    correct = sum(1 for r in rows if r["metrics"]["correct"])
    retries = sum(r["metrics"]["retries"] for r in rows)
    replans = sum(r["metrics"]["replans"] for r in rows)
    post_success_steps = sum(r["metrics"]["post_success_steps"] for r in rows)

    return {
        "cases": cases,
        "correct": correct,
        "avg_steps": round(total_steps / cases, 2) if cases else 0.0,
        "avg_llm_calls": round(total_llm_calls / cases, 2) if cases else 0.0,
        "retries": retries,
        "replans": replans,
        "post_success_steps": post_success_steps,
    }


def main():
    baseline = load("results/baseline.json")
    aegis = load("results/aegis.json")

    b = summarize_rows(baseline)
    a = summarize_rows(aegis)

    print("=" * 60)
    print("BASELINE")
    print("=" * 60)
    print(b)

    print("\n" + "=" * 60)
    print("AEGIS")
    print("=" * 60)
    print(a)

    print("\n" + "=" * 60)
    print("DELTA")
    print("=" * 60)
    print({
        "step_reduction": round(b["avg_steps"] - a["avg_steps"], 2),
        "llm_call_reduction": round(b["avg_llm_calls"] - a["avg_llm_calls"], 2),
        "retry_reduction": b["retries"] - a["retries"],
        "replan_reduction": b["replans"] - a["replans"],
        "post_success_step_reduction": b["post_success_steps"] - a["post_success_steps"],
        "correct_delta": a["correct"] - b["correct"],
    })


if __name__ == "__main__":
    main()