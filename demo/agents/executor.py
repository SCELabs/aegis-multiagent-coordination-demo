from __future__ import annotations

from demo.models import ActionType, CaseInput, ControlDirectives, ExecutionResult, PlanAction, RunState


def _base_policy_decision(case: CaseInput) -> str:
    if case.explicit_exception:
        return "approve"
    if case.item_damaged and case.days_since_purchase <= 30 and not case.used_item:
        return "approve"
    if case.used_item:
        return "deny"
    if case.days_since_purchase > 30 and not case.item_damaged:
        return "deny"
    if case.customer_tier == "premium" and case.item_damaged and case.days_since_purchase > 30:
        return "escalate"
    return "deny"


def execute_action(state: RunState, plan: PlanAction, control: ControlDirectives) -> ExecutionResult:
    case = state.case
    decision = _base_policy_decision(case)
    policy_applied = "standard_refund_policy"
    exception_used = False
    summary = ""

    if plan.action_type == ActionType.GATHER_FACTS:
        summary = (
            f"Gathered case facts: tier={case.customer_tier}, days={case.days_since_purchase}, "
            f"damaged={case.item_damaged}, used={case.used_item}, prior_refunds={case.prior_refunds}, "
            f"explicit_exception={case.explicit_exception}."
        )
        return ExecutionResult(
            summary=summary,
            proposed_decision="needs_replan",
            policy_applied="fact_collection",
            exception_used=False,
            confidence=0.92,
        )

    if plan.action_type == ActionType.APPLY_POLICY:
        # Mild realistic drift in baseline mode:
        # borderline premium + damaged cases may be "helpfully" over-approved.
        if (
            control.mode == "baseline"
            and case.customer_tier == "premium"
            and case.item_damaged
            and case.days_since_purchase > 30
        ):
            decision = "approve"

        summary = "Applied core refund policy to current case facts."
        return ExecutionResult(
            summary=summary,
            proposed_decision=decision,
            policy_applied=policy_applied,
            exception_used=False,
            confidence=0.72 if control.mode == "baseline" else 0.84,
        )

    if plan.action_type == ActionType.CHECK_EXCEPTION:
        if case.explicit_exception:
            decision = "approve"
            exception_used = True
            summary = "Explicit exception found in case notes and applied."
        elif case.customer_tier == "premium" and case.item_damaged and case.days_since_purchase > 30:
            decision = "escalate"
            summary = "No explicit exception found, but premium damaged edge case merits escalation review."
        else:
            summary = "No qualifying exception found. Fall back to standard policy decision."

        return ExecutionResult(
            summary=summary,
            proposed_decision=decision,
            policy_applied="exception_review",
            exception_used=exception_used,
            confidence=0.69 if control.mode == "baseline" else 0.86,
        )

    if plan.action_type == ActionType.REPLAN:
        summary = "Replanned the next step after validator challenge."
        return ExecutionResult(
            summary=summary,
            proposed_decision=state.last_execution.proposed_decision if state.last_execution else "needs_replan",
            policy_applied="replan",
            exception_used=False,
            confidence=0.60,
        )

    # FINALIZE_DECISION
    if state.last_execution and state.last_execution.proposed_decision != "needs_replan":
        decision = state.last_execution.proposed_decision

    summary = "Finalized the case decision from collected evidence and prior checks."
    return ExecutionResult(
        summary=summary,
        proposed_decision=decision,
        policy_applied="finalization",
        exception_used=state.last_execution.exception_used if state.last_execution else False,
        confidence=0.78 if control.mode == "baseline" else 0.90,
    )
