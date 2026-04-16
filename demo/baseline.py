from __future__ import annotations

from demo.config import DEFAULT_CONFIG, DemoConfig
from demo.models import ControlDirectives
from demo.tasks import get_cases
from demo.workflow import run_case


def build_baseline_control(config: DemoConfig = DEFAULT_CONFIG) -> ControlDirectives:
    return ControlDirectives(
        mode="baseline",
        temperature=config.baseline_temperature,
        validator_strictness=config.baseline_validator_strictness,
        retry_bias=config.baseline_retry_bias,
        replan_bias=config.baseline_replan_bias,
        stop_on_valid=False,
        suppress_duplicate_actions=False,
        max_retries_override=config.max_retries,
        max_steps_override=config.max_steps,
        notes=[
            "Baseline mode: no runtime stabilization.",
            "Allow retry/replan churn when signals are noisy.",
        ],
    )


def run_baseline(config: DemoConfig = DEFAULT_CONFIG):
    results = []
    control = build_baseline_control(config)

    for case in get_cases():
        state, metrics = run_case(case, control, config)
        results.append(
            {
                "case_id": case.case_id,
                "state": state,
                "metrics": metrics,
            }
        )

    return results
