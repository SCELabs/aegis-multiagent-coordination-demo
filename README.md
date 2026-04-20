# Aegis Multi-Agent Coordination Demo

This repository shows a **multi-agent coordination workflow** running in two modes:

- baseline (no runtime stabilization)
- with Aegis runtime stabilization

The core workflow is unchanged in both runs. Aegis is inserted at the coordination boundary and returns runtime guidance that the loop applies.

---

## What this demo proves

- The same planner/executor/validator loop can run with and without Aegis.
- Aegis can stabilize runtime behavior (retries, replans, drift) without changing the underlying model logic.
- You can inspect the returned `AegisResult` surface (`actions`, `trace`, `metrics`, `used_fallback`, `explanation`, `scope`, `scope_data`).

---

## Where Aegis is inserted

Aegis is called at the **coordination step boundary** using the **step scope**:

- `client.auto().step(...)`

This is the smallest correct scope for this demo because the intervention point is the coordinator behavior (not direct LLM prompting and not retrieval flow).

---

## Runtime SDK surface used

```python
from aegis import AegisClient, AegisConfig

client = AegisClient(
    api_key=os.environ["AEGIS_API_KEY"],
    base_url=os.environ["AEGIS_BASE_URL"],
    config=AegisConfig(mode="balanced"),
)

result = client.auto().step(...)
```

The demo maps the returned `AegisResult` into loop controls and logs key signals from:

- `result.actions`
- `result.trace`
- `result.metrics`
- `result.explanation`
- `result.used_fallback`
- `result.scope`
- `result.scope_data`
- `result.debug_summary()` (when available)

---

## Workflow summary

The demo workflow has four roles:

- Planner → picks next action
- Executor → proposes decision
- Validator → checks decision and requests retry/replan when needed
- Coordinator loop → advances the run until completion

Aegis stabilizes the runtime behavior of the coordinator loop by reducing unnecessary retries/replans and helping terminate cleanly on valid outcomes.

---

## Setup

### 1) Clone

```bash
git clone https://github.com/SCELabs/aegis-multiagent-coordination-demo.git
cd aegis-multiagent-coordination-demo
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment

Copy `.env.example` to `.env` and set values:

```bash
cp .env.example .env
```

Required:

- `AEGIS_API_KEY`
- `AEGIS_BASE_URL`

`AEGIS_BASE_URL` is explicit and configurable. If your Aegis backend is local, set a localhost URL; otherwise set your deployed endpoint.

---

## Run

### Baseline

```bash
python scripts/run_baseline.py
```

### With Aegis stabilization

```bash
python scripts/run_aegis.py
```

### Compare outputs

```bash
python scripts/compare_runs.py
```

Artifacts are written to `results/`.

---

## Notes on behavior

- If Aegis credentials are not configured (or a live call fails), the demo uses an internal fallback stabilization profile so the run remains executable.
- The fallback path is explicitly logged in run notes.
- The purpose of this fallback is demo continuity, not replacing live Aegis responses.

---

## Aegis client SDK

- SDK/package: `scelabs-aegis`
- Source repo: https://github.com/SCELabs/aegis-client
