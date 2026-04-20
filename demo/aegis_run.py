from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

from demo.config import DEFAULT_CONFIG, DemoConfig
from demo.models import ControlDirectives, RunState
from demo.tasks import get_cases
from demo.workflow import run_case


load_dotenv(dotenv_path=Path(".env"))


BASE_PROMPT = (
    "You are stabilizing a multi-agent case resolution workflow with a coordinator, "
    "planner, executor, and validator. The goal is to reduce unnecessary retries, "
    "replans, duplicate work, and post-success churn while preserving correct outcomes."
)


def _fallback_aegis_control(config: DemoConfig = DEFAULT_CONFIG) -> ControlDirectives:
    return ControlDirectives(
        mode="aegis",
        temperature=config.aegis_temperature,
        validator_strictness=config.aegis_validator_strictness,
        retry_bias=config.aegis_retry_bias,
        replan_bias=config.aegis_replan_bias,
        stop_on_valid=True,
        suppress_duplicate_actions=True,
        max_retries_override=min(1, config.max_retries),
        max_steps_override=config.max_steps,
        notes=[],
    )


def _maybe_get(obj: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if isinstance(obj, dict) and name in obj:
            return obj[name]
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    return default


def _result_to_control(result: Any, config: DemoConfig) -> ControlDirectives:
    control = _fallback_aegis_control(config)

    scope_data = _maybe_get(result, "scope_data", default={}) or {}
    output = _maybe_get(result, "output", default={}) or {}

    generation = _maybe_get(scope_data, "generation", default={}) or {}
    loop_controls = _maybe_get(scope_data, "loop_controls", default={}) or {}

    control.temperature = _coerce_float(
        _maybe_get(generation, "temperature", default=control.temperature),
        control.temperature,
    )
    control.validator_strictness = _coerce_float(
        _maybe_get(loop_controls, "validator_strictness", default=control.validator_strictness),
        control.validator_strictness,
    )
    control.retry_bias = _coerce_float(
        _maybe_get(loop_controls, "retry_bias", default=control.retry_bias),
        control.retry_bias,
    )
    control.replan_bias = _coerce_float(
        _maybe_get(loop_controls, "replan_bias", default=control.replan_bias),
        control.replan_bias,
    )
    control.stop_on_valid = _coerce_bool(
        _maybe_get(loop_controls, "stop_on_valid", default=control.stop_on_valid),
        control.stop_on_valid,
    )
    control.suppress_duplicate_actions = _coerce_bool(
        _maybe_get(
            loop_controls,
            "suppress_duplicate_actions",
            default=control.suppress_duplicate_actions,
        ),
        control.suppress_duplicate_actions,
    )

    max_retries_override = _maybe_get(loop_controls, "max_retries", "max_retries_override", default=None)
    if max_retries_override is not None:
        control.max_retries_override = int(max_retries_override)

    max_steps_override = _maybe_get(loop_controls, "max_steps", "max_steps_override", default=None)
    if max_steps_override is not None:
        control.max_steps_override = int(max_steps_override)

    scope = _maybe_get(result, "scope", default="unknown")
    control.notes.append(f"Aegis scope: {scope}")

    explanation = _maybe_get(result, "explanation", default=None)
    if explanation:
        control.notes.append(f"Aegis explanation: {explanation}")

    used_fallback = _coerce_bool(_maybe_get(result, "used_fallback", default=False), False)
    control.notes.append(f"Aegis used_fallback: {used_fallback}")

    actions = _maybe_get(result, "actions", default=[]) or []
    if actions:
        action_types = []
        for action in actions:
            action_type = _maybe_get(action, "type", default=None)
            if action_type:
                action_types.append(action_type)

        if action_types:
            control.notes.append(f"Aegis actions: {', '.join(action_types)}")

        if "stabilize_system" in action_types:
            control.stop_on_valid = True
            control.retry_bias = min(control.retry_bias, 0.2)
        if "increase_constraints" in action_types:
            control.replan_bias = min(control.replan_bias, 0.2)
            control.suppress_duplicate_actions = True
        if "adjust_flexibility" in action_types:
            control.validator_strictness = min(control.validator_strictness, 0.6)

    trace = _maybe_get(result, "trace", default=[]) or []
    if trace:
        control.notes.append(f"Aegis trace events: {len(trace)}")

    metrics = _maybe_get(result, "metrics", default={}) or {}
    confidence = _maybe_get(metrics, "confidence", default=None)
    if confidence is not None:
        control.notes.append(f"Aegis confidence: {confidence}")

    debug_summary = _maybe_get(result, "debug_summary", default=None)
    if callable(debug_summary):
        control.notes.append(f"Aegis debug: {debug_summary()}")

    final_answer = _maybe_get(result, "final_answer", default=None)
    if final_answer:
        control.notes.append(f"Aegis final_answer: {final_answer}")
    elif output:
        control.notes.append("Aegis output returned for step scope.")

    return control


def build_aegis_control(
    state: Optional[RunState] = None,
    config: DemoConfig = DEFAULT_CONFIG,
) -> ControlDirectives:
    api_key = os.getenv("AEGIS_API_KEY")
    base_url = os.getenv("AEGIS_BASE_URL")

    if not api_key or not base_url:
        control = _fallback_aegis_control(config)
        if not api_key:
            control.notes.append("AEGIS_API_KEY not set; using fallback profile.")
        if not base_url:
            control.notes.append("AEGIS_BASE_URL not set; using fallback profile.")
        return control

    try:
        from aegis import AegisClient, AegisConfig

        client = AegisClient(
            api_key=api_key,
            base_url=base_url,
            config=AegisConfig(mode="balanced"),
        )

        symptoms = [
            "agent_disagreement",
            "excessive_replans",
            "post_success_churn",
            "duplicate_work",
        ]
        severity = "medium"

        step_input: dict[str, Any] = {
            "workflow": "multi_agent_case_resolution",
            "agents": ["planner", "executor", "validator"],
            "target_outcome": "same_correct_result_with_less_execution_waste",
            "base_prompt": BASE_PROMPT,
        }

        if state is not None:
            step_input.update(
                {
                    "case_id": state.case.case_id,
                    "customer_tier": state.case.customer_tier,
                    "days_since_purchase": state.case.days_since_purchase,
                    "item_damaged": state.case.item_damaged,
                    "used_item": state.case.used_item,
                    "explicit_exception": state.case.explicit_exception,
                    "step_index": state.step_index,
                    "retries": state.retries,
                    "replans": state.replans,
                    "action_history": state.action_history,
                    "decision_history": state.decision_history,
                    "success_declared_at_step": state.success_declared_at_step,
                }
            )

            if state.retries > 0:
                symptoms.append("excessive_retries")
            if state.success_declared_at_step is not None:
                symptoms.append("post_success_churn")

        result = client.auto().step(
            step_name="coordinator_stabilization",
            step_input=step_input,
            symptoms=symptoms,
            severity=severity,
        )

        control = _result_to_control(result, config)
        control.mode = "aegis"
        control.notes.append("Control derived from Aegis step runtime result.")
        return control

    except Exception as e:
        control = _fallback_aegis_control(config)
        control.notes.extend(
            [
                "Fallback Aegis profile.",
                "Use lower retry/replan bias and stop cleanly on valid outcomes.",
                f"Live Aegis call failed; using fallback profile. Error: {e}",
            ]
        )
        return control


def run_aegis(config: DemoConfig = DEFAULT_CONFIG):
    results = []

    for case in get_cases():
        state = None
        control = build_aegis_control(state=state, config=config)
        state, metrics = run_case(case, control, config)
        results.append(
            {
                "case_id": case.case_id,
                "state": state,
                "metrics": metrics,
            }
        )

    return results
