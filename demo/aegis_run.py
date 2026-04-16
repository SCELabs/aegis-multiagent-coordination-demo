from __future__ import annotations

import os
from typing import Any, Optional
from pathlib import Path

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


def _derive_loop_controls_from_plan(plan: Any, control: ControlDirectives, config: DemoConfig) -> None:
    status = _maybe_get(plan, "status", default="unknown")
    actions = _maybe_get(plan, "actions", default=[]) or []
    prediction = _maybe_get(plan, "prediction", default=None)
    raw = _maybe_get(plan, "raw", default={}) or {}
    confidence = _maybe_get(raw, "confidence", default=None)

    confidence_val = _coerce_float(confidence, 0.75)

    control.notes.append(f"Aegis status: {status}")
    control.notes.append(f"Aegis confidence: {confidence_val}")

    action_types = set()
    for action in actions:
        action_type = _maybe_get(action, "type", default=None)
        if action_type:
            action_types.add(action_type)

    # Derive behavior from live plan semantics instead of guessing raw fields.
    if status == "stable":
        control.stop_on_valid = True
        control.suppress_duplicate_actions = True
        control.max_retries_override = min(1, config.max_retries)

        # Stable system + medium confidence => keep loop tighter.
        control.retry_bias = 0.15 if confidence_val >= 0.7 else 0.25
        control.replan_bias = 0.15 if confidence_val >= 0.7 else 0.25

    if "stabilize_system" in action_types:
        control.stop_on_valid = True
        control.retry_bias = min(control.retry_bias, 0.2)
        control.notes.append("Derived: stabilize_system -> suppress unnecessary retries.")

    if "increase_constraints" in action_types:
        control.replan_bias = min(control.replan_bias, 0.2)
        control.suppress_duplicate_actions = True
        control.notes.append("Derived: increase_constraints -> tighter coordination and dedupe.")

    if "adjust_flexibility" in action_types:
        # Allow some flexibility without reopening the loop too much.
        control.validator_strictness = min(control.validator_strictness, 0.6)
        control.notes.append("Derived: adjust_flexibility -> slightly relax validator rigidity.")

    if prediction is not None:
        control.notes.append(f"Aegis prediction: {prediction}")


def _plan_to_control(plan: Any, config: DemoConfig) -> ControlDirectives:
    control = _fallback_aegis_control(config)

    controls = _maybe_get(plan, "controls", default={}) or {}
    generation = _maybe_get(controls, "generation", default={}) or {}
    prompt_controls = _maybe_get(controls, "prompt", default={}) or {}
    raw = _maybe_get(plan, "raw", default={}) or {}

    # Real live fields confirmed from AegisPlan output.
    control.temperature = _coerce_float(
        _maybe_get(generation, "temperature", default=control.temperature),
        control.temperature,
    )

    # Keep top_p only as note for now since ControlDirectives does not store it.
    top_p = _maybe_get(generation, "top_p", default=None)
    if top_p is not None:
        control.notes.append(f"Aegis top_p: {top_p}")

    prompt_suffix = _maybe_get(prompt_controls, "suffix", default=None)
    if prompt_suffix:
        control.notes.append(f"Aegis prompt suffix: {prompt_suffix}")

    summary = _maybe_get(raw, "summary", default=None)
    cause = _maybe_get(raw, "cause", default=None)

    if summary:
        control.notes.append(f"Plan summary: {summary}")
    if cause:
        control.notes.append(f"Plan cause: {cause}")

    _derive_loop_controls_from_plan(plan, control, config)
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
        from aegis import AegisClient

        client = AegisClient(api_key=api_key, base_url=base_url)

        symptoms = [
            "agent_disagreement",
            "excessive_replans",
            "post_success_churn",
            "duplicate_work",
        ]
        severity = "medium"

        metadata = {
            "workflow": "multi_agent_case_resolution",
            "agents": ["planner", "executor", "validator"],
            "target_outcome": "same_correct_result_with_less_execution_waste",
        }

        if state is not None:
            metadata.update(
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

        plan = client.auto(
            system_type="multi_agent",
            base_prompt=BASE_PROMPT,
            symptoms=symptoms,
            severity=severity,
            metadata=metadata,
        )

        control = _plan_to_control(plan, config)
        control.mode = "aegis"
        control.notes.append("Control derived from live Aegis plan.")
        return control

    except Exception as e:
        control = _fallback_aegis_control(config)
        control.notes.extend([
            "Fallback Aegis profile.",
            "Use lower retry/replan bias and stop cleanly on valid outcomes.",
            f"Live Aegis call failed; using fallback profile. Error: {e}",
        ])
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
