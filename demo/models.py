from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Decision(str, Enum):
    APPROVE = "approve"
    DENY = "deny"
    ESCALATE = "escalate"
    NEEDS_REPLAN = "needs_replan"


class ActionType(str, Enum):
    GATHER_FACTS = "gather_facts"
    APPLY_POLICY = "apply_policy"
    CHECK_EXCEPTION = "check_exception"
    FINALIZE_DECISION = "finalize_decision"
    REPLAN = "replan"


@dataclass
class CaseInput:
    case_id: str
    title: str
    customer_tier: str
    days_since_purchase: int
    item_damaged: bool
    used_item: bool
    prior_refunds: int
    explicit_exception: bool
    notes: str
    expected_decision: str


@dataclass
class PlanAction:
    action_type: ActionType
    rationale: str
    target_decision: Optional[str] = None
    confidence: float = 0.0


@dataclass
class ExecutionResult:
    summary: str
    proposed_decision: str
    policy_applied: str
    exception_used: bool
    confidence: float = 0.0


@dataclass
class ValidationResult:
    valid: bool
    agreement: bool
    validator_decision: str
    feedback: str
    should_retry: bool = False
    should_replan: bool = False


@dataclass
class ControlDirectives:
    mode: str = "baseline"
    temperature: float = 0.7
    validator_strictness: float = 0.7
    retry_bias: float = 0.7
    replan_bias: float = 0.7
    stop_on_valid: bool = False
    suppress_duplicate_actions: bool = False
    max_retries_override: Optional[int] = None
    max_steps_override: Optional[int] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class RunState:
    case: CaseInput
    step_index: int = 0
    retries: int = 0
    replans: int = 0
    completed: bool = False
    success_declared_at_step: Optional[int] = None
    final_decision: Optional[str] = None
    last_plan: Optional[PlanAction] = None
    last_execution: Optional[ExecutionResult] = None
    last_validation: Optional[ValidationResult] = None
    action_history: List[str] = field(default_factory=list)
    decision_history: List[str] = field(default_factory=list)
    event_log: List[Dict[str, Any]] = field(default_factory=list)

    def log_event(self, kind: str, payload: Dict[str, Any]) -> None:
        self.event_log.append(
            {
                "step": self.step_index,
                "kind": kind,
                "payload": payload,
            }
        )
