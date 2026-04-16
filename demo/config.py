from dataclasses import dataclass


@dataclass(frozen=True)
class DemoConfig:
    model_name: str = "gpt-4.1-mini"
    max_steps: int = 8
    max_retries: int = 3
    baseline_temperature: float = 0.8
    aegis_temperature: float = 0.3
    baseline_validator_strictness: float = 0.8
    aegis_validator_strictness: float = 0.55
    baseline_retry_bias: float = 0.75
    aegis_retry_bias: float = 0.35
    baseline_replan_bias: float = 0.7
    aegis_replan_bias: float = 0.3


DEFAULT_CONFIG = DemoConfig()
