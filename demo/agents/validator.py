from __future__ import annotations

from demo.models import CaseInput, ControlDirectives, ExecutionResult, ValidationResult


def _expected_policy_outcome(case: CaseInput) -> str:
    if case.explicit_exception:
        return "approve"
    if case.item_damaged and case.days_since_purchase <= 30 and not case.used_item:
        return "approve"
    if case.used_item:
        return "deny"
    if case.customer_tier == "premium" and case.item_damaged and case.days_since_purchase > 30:
        return "escalate"
    if case.days_since_purchase > 30 and not case.item_damaged:
        return "deny"
    return "deny"


def validate_execution(case: CaseInput, execution: ExecutionResult, control: ControlDirectives) -> ValidationResult:
    expected = _expected_policy_outcome(case)
    agreement = execution.proposed_decision == expected

    borderline_case = (
        case.customer_tier == "premium"
        and case.item_damaged
        and case.days_since_purchase > 30
    )

    if agreement:
        if control.stop_on_valid:
            return ValidationResult(
                valid=True,
                agreement=True,
                validator_decision=expected,
                feedback="Execution matches expected policy outcome. Stop cleanly.",
                should_retry=False,
                should_replan=False,
            )

        # Baseline anti-pattern:
        # a correct final answer can still trigger one more pass if the validator
        # feels the justification/confidence is soft, especially on approve/escalate outcomes.
        soft_confidence_final = (
            control.mode == "baseline"
            and execution.policy_applied == "finalization"
            and execution.proposed_decision in {"approve", "escalate"}
            and execution.confidence < 0.80
        )

        if soft_confidence_final:
            return ValidationResult(
                valid=True,
                agreement=True,
                validator_decision=expected,
                feedback="Decision looks correct, but confidence is soft. Retry once before closing.",
                should_retry=True,
                should_replan=False,
            )

        # Borderline correct answers may still get over-checked in baseline mode.
        if control.mode == "baseline" and borderline_case and execution.confidence < 0.80:
            return ValidationResult(
                valid=True,
                agreement=True,
                validator_decision=expected,
                feedback="Decision is likely correct, but confidence is soft. Recheck before closing.",
                should_retry=True,
                should_replan=False,
            )

        return ValidationResult(
            valid=True,
            agreement=True,
            validator_decision=expected,
            feedback="Execution matches expected policy outcome.",
            should_retry=False,
            should_replan=False,
        )

    if borderline_case and execution.proposed_decision == "approve":
        if control.validator_strictness >= 0.7:
            return ValidationResult(
                valid=False,
                agreement=False,
                validator_decision=expected,
                feedback="Premium damaged edge case outside window should escalate, not approve.",
                should_retry=False,
                should_replan=True,
            )

    if execution.proposed_decision == "needs_replan":
        return ValidationResult(
            valid=False,
            agreement=False,
            validator_decision=expected,
            feedback="No decision was produced. Continue workflow.",
            should_retry=False,
            should_replan=False,
        )

    should_retry = control.retry_bias >= 0.5
    should_replan = control.replan_bias >= 0.5

    return ValidationResult(
        valid=False,
        agreement=False,
        validator_decision=expected,
        feedback=f"Decision mismatch. Expected {expected}, got {execution.proposed_decision}.",
        should_retry=should_retry,
        should_replan=should_replan,
    )
