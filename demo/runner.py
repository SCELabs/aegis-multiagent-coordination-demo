from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from demo.baseline import run_baseline
from demo.aegis_run import run_aegis


RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)


def serialize_run(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for item in results:
        metrics = item["metrics"]
        state = item["state"]
        rows.append(
            {
                "case_id": item["case_id"],
                "metrics": metrics.to_dict(),
                "final_decision": state.final_decision,
                "event_log": state.event_log,
                "notes": getattr(metrics, "notes", []),
            }
        )
    return rows


def save_results(filename: str, results: List[Dict[str, Any]]) -> Path:
    path = RESULTS_DIR / filename
    path.write_text(json.dumps(serialize_run(results), indent=2), encoding="utf-8")
    return path


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    count = len(results)
    agg = {
        "cases": count,
        "completed": 0,
        "correct": 0,
        "total_steps": 0,
        "total_llm_calls": 0,
        "retries": 0,
        "replans": 0,
        "validator_rejections": 0,
        "duplicate_actions": 0,
        "post_success_steps": 0,
        "avg_agreement_rate": 0.0,
    }

    agreement_total = 0.0

    for item in results:
        m = item["metrics"]
        agg["completed"] += int(m.completed)
        agg["correct"] += int(m.correct)
        agg["total_steps"] += m.total_steps
        agg["total_llm_calls"] += m.total_llm_calls
        agg["retries"] += m.retries
        agg["replans"] += m.replans
        agg["validator_rejections"] += m.validator_rejections
        agg["duplicate_actions"] += m.duplicate_actions
        agg["post_success_steps"] += m.post_success_steps
        agreement_total += m.agreement_rate

    if count:
        agg["avg_agreement_rate"] = round(agreement_total / count, 3)
        agg["avg_steps"] = round(agg["total_steps"] / count, 2)
        agg["avg_llm_calls"] = round(agg["total_llm_calls"] / count, 2)

    return agg


def run_mode(mode: str):
    if mode == "baseline":
        return run_baseline()
    if mode == "aegis":
        return run_aegis()
    raise ValueError(f"Unsupported mode: {mode}")
