# Aegis Multi-Agent Coordination Demo

Your multi-agent system is probably working.

But it's wasting steps, retrying unnecessarily, and continuing long after the correct answer is already found.

This repo shows that clearly — and fixes it.

---

## ⚡ What this demo proves

We run the **same multi-agent system twice**:

* once as baseline
* once with Aegis

Same logic. Same cases. Same outcomes.

Only difference:

Aegis sits above the loop and stabilizes execution.

---

## 🧠 The system

A realistic multi-agent workflow:

* Planner → decides next step
* Executor → applies policy and proposes decision
* Validator → checks correctness and triggers retries/replans
* Coordinator → manages the loop

This is intentionally designed to resemble real-world systems:

* agent disagreement
* validator second-guessing
* unnecessary replanning
* post-success drift

---

## 📉 Baseline behavior

The system works… but:

* agents overthink and re-check decisions
* validator triggers unnecessary replans
* duplicate actions occur
* the system continues after success
* LLM calls accumulate with no gain

---

## ⚙️ With Aegis

Aegis analyzes the system and returns:

* runtime controls (temperature, prompt constraints)
* stabilization actions
* coordination guidance

We translate that into:

* fewer retries
* fewer replans
* no duplicate work
* clean termination after success

---

## 📊 Results

BASELINE

* 5/5 correct
* 4.2 average steps
* 12.6 average LLM calls
* 2 retries
* 7 replans
* 5 post-success steps

WITH AEGIS

* 5/5 correct
* 2.0 average steps
* 6.0 average LLM calls
* 0 retries
* 0 replans
* 0 post-success steps

RESULT

* 52% fewer steps
* 52% fewer LLM calls
* same completion quality

---

## 🔍 What’s actually happening

Aegis does not make your model smarter.

It makes your system more coherent.

In this demo:

* Aegis detects instability patterns:

  * over-replanning
  * unnecessary retries
  * rigid vs flexible mismatch

* Returns a plan:

  * adjust flexibility
  * stabilize execution
  * increase coordination constraints

* The coordinator translates that into behavior:

  * tighter retry control
  * reduced replanning
  * stop after valid outcome

---

## 🧩 Key idea

Same intelligence. Better execution.

Most systems don’t fail because the model is wrong.

They fail because:

* they don’t know when to stop
* they re-run good answers
* they drift under uncertainty

Aegis fixes that layer.

---

## 🚀 Try it yourself

### 1. Clone

git clone https://github.com/SCELabs/aegis-multiagent-coordination-demo.git
cd aegis-multiagent-coordination-demo

### 2. Install

pip install -r requirements.txt
pip install scelabs-aegis

### 3. Configure

Create a `.env` file in the root:

AEGIS_API_KEY=your_key_here
AEGIS_BASE_URL=https://your-aegis-backend-url

### 4. Run baseline

python scripts/run_baseline.py

### 5. Run with Aegis

python scripts/run_aegis.py

### 6. Compare

python scripts/compare_runs.py

---

## 🔗 Get started with Aegis

Install the SDK:

pip install scelabs-aegis

Explore the SDK and examples here:
https://github.com/SCELabs/aegis-client

---

## 🧠 How Aegis fits into your system

You don’t rewrite your system.

You don’t retrain your models.

You add Aegis above your loop:

* observe behavior
* detect instability
* apply runtime controls

That’s it.

---

## 🎯 When Aegis is most useful

* multi-agent workflows
* tool-using agents
* retry-heavy systems
* systems with validation loops
* anything with coordination drift

---

## 📌 Final takeaway

If your system works but feels inefficient, unstable, or inconsistent…

You don’t need a bigger model.

You need a control layer.

That’s what Aegis is.
