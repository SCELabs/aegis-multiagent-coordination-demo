from __future__ import annotations

from demo.agents.executor import execute_action
from demo.agents.planner import plan_next_action
from demo.agents.validator import validate_execution
from demo.config import DemoConfig
from demo.metrics import RunMetrics
from demo.models import CaseInput, ControlDirectives, RunState


def build_initial_state(case: CaseInput) -> RunState:
    return RunState(case=case)


def run_case(case: CaseInput, control: ControlDirectives, config: DemoConfig) -> tuple[RunState, RunMetrics]:
    state = build_initial_state(case)
    metrics = RunMetrics(case_id=case.case_id, mode=control.mode)
    metrics.notes.extend(control.notes)

    max_steps = control.max_steps_override or config.max_steps
    max_retries = control.max_retries_override or config.max_retries

    while not state.completed and state.step_index < max_steps:
        state.step_index += 1

        plan = plan_next_action(state, control)
        metrics.record_llm_call()

        execution = execute_action(state, plan, control)
        metrics.record_llm_call()

        validation = validate_execution(case, execution, control)
        metrics.record_llm_call()

        state.last_plan = plan
        state.last_execution = execution
        state.last_validation = validation
        state.action_history.append(plan.action_type.value)
        state.decision_history.append(execution.proposed_decision)

        state.log_event(
            "iteration",
            {
                "plan_action": plan.action_type.value,
                "plan_rationale": plan.rationale,
                "execution_decision": execution.proposed_decision,
                "validation_decision": validation.validator_decision,
                "validation_valid": validation.valid,
                "retry": validation.should_retry,
                "replan": validation.should_replan,
            },
        )

        metrics.record_step(state, plan, execution, validation)

        if validation.valid and execution.proposed_decision != "needs_replan":
            if state.success_declared_at_step is None:
                state.success_declared_at_step = state.step_index

            if control.stop_on_valid:
                state.completed = True
                state.final_decision = execution.proposed_decision
                break

        if validation.should_replan:
            state.replans += 1

        if validation.should_retry:
            state.retries += 1

        if state.retries > max_retries:
            state.completed = True
            state.final_decision = validation.validator_decision
            state.log_event(
                "forced_termination",
                {"reason": "retry_limit_exceeded", "final_decision": state.final_decision},
            )
            break

        # Complete when we reach a valid finalization or when finalization agrees.
        if (
            plan.action_type.value == "finalize_decision"
            and validation.valid
            and execution.proposed_decision != "needs_replan"
        ):
            state.completed = True
            state.final_decision = execution.proposed_decision
            break

    if not state.completed:
        if state.last_validation:
            state.final_decision = state.last_validation.validator_decision
        elif state.last_execution:
            state.final_decision = state.last_execution.proposed_decision
        else:
            state.final_decision = "deny"
        state.completed = True
        state.log_event(
            "forced_termination",
            {"reason": "max_steps_reached", "final_decision": state.final_decision},
        )

    metrics.finalize(state)
    return state, metrics
