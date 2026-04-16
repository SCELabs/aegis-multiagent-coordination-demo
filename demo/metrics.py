from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from demo.models import ExecutionResult, PlanAction, RunState, ValidationResult


@dataclass
class RunMetrics:
    case_id: str
    mode: str
    total_steps: int = 0
    total_llm_calls: int = 0
    retries: int = 0
    replans: int = 0
    validator_rejections: int = 0
    duplicate_actions: int = 0
    post_success_steps: int = 0
    completed: bool = False
    final_decision: Optional[str] = None
    expected_decision: Optional[str] = None
    correct: bool = False
    agreement_events: int = 0
    disagreement_events: int = 0
    action_sequence: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def record_llm_call(self, count: int = 1) -> None:
        self.total_llm_calls += count

    def record_step(
        self,
        state: RunState,
        plan: PlanAction,
        execution: ExecutionResult,
        validation: ValidationResult,
    ) -> None:
        self.total_steps += 1
        self.action_sequence.append(plan.action_type.value)

        if validation.should_retry:
            self.retries += 1
        if validation.should_replan:
            self.replans += 1
        if not validation.valid:
            self.validator_rejections += 1

        if validation.agreement:
            self.agreement_events += 1
        else:
            self.disagreement_events += 1

        if state.success_declared_at_step is not None and state.step_index > state.success_declared_at_step:
            self.post_success_steps += 1

        if self.action_sequence.count(plan.action_type.value) > 1:
            self.duplicate_actions += 1

    def finalize(self, state: RunState) -> None:
        self.completed = state.completed
        self.final_decision = state.final_decision
        self.expected_decision = state.case.expected_decision
        self.correct = state.final_decision == state.case.expected_decision

    @property
    def agreement_rate(self) -> float:
        total = self.agreement_events + self.disagreement_events
        return self.agreement_events / total if total else 0.0

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["agreement_rate"] = round(self.agreement_rate, 3)
        return data
