from __future__ import annotations

from demo.models import ActionType, CaseInput, ControlDirectives, PlanAction, RunState


def _needs_exception_check(case: CaseInput) -> bool:
    return case.explicit_exception or (
        case.customer_tier == "premium" and case.days_since_purchase > 30 and case.item_damaged
    )


def _should_finalize(state: RunState) -> bool:
    return len(state.action_history) >= 2 and (
        "apply_policy" in state.action_history or "check_exception" in state.action_history
    )


def plan_next_action(state: RunState, control: ControlDirectives) -> PlanAction:
    case = state.case

    if state.last_validation and state.last_validation.should_replan:
        return PlanAction(
            action_type=ActionType.REPLAN,
            rationale="Validator requested replanning due to insufficient confidence or policy mismatch.",
            confidence=0.62,
        )

    if not state.action_history:
        return PlanAction(
            action_type=ActionType.GATHER_FACTS,
            rationale="Start by gathering the case facts and identifying relevant policy signals.",
            confidence=0.88,
        )

    if "gather_facts" in state.action_history and "apply_policy" not in state.action_history:
        return PlanAction(
            action_type=ActionType.APPLY_POLICY,
            rationale="Facts are collected. Apply core refund policy before considering edge handling.",
            confidence=0.83,
        )

    if _needs_exception_check(case) and "check_exception" not in state.action_history:
        return PlanAction(
            action_type=ActionType.CHECK_EXCEPTION,
            rationale="Case includes exception pressure or premium edge conditions requiring exception review.",
            confidence=0.74,
        )

    if _should_finalize(state):
        return PlanAction(
            action_type=ActionType.FINALIZE_DECISION,
            rationale="Enough evidence has been collected to finalize the case outcome.",
            confidence=0.79,
        )

    # Baseline-style mild overplanning:
    # if retry/replan bias is high, planner may revisit policy after already doing enough.
    if control.replan_bias >= 0.6:
        return PlanAction(
            action_type=ActionType.APPLY_POLICY,
            rationale="Revisit policy interpretation to confirm consistency before finalizing.",
            confidence=0.58,
        )

    return PlanAction(
        action_type=ActionType.FINALIZE_DECISION,
        rationale="Default to finalization after prior review steps.",
        confidence=0.68,
    )
