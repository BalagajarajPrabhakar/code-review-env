---
title: AI Code Review Env
emoji: 🔍
colorFrom: blue
colorTo: green
sdk: docker
app_file: server/app.py
pinned: false
tags:
  - openenv
  - code-review
  - reinforcement-learning
  - agent-evaluation
---

# 🔍 AI Code Review Environment (OpenEnv)

An **OpenEnv-compatible** reinforcement-learning environment where AI agents
learn to perform real-world pull-request code reviews — identifying bugs,
security vulnerabilities, performance bottlenecks, and design smells.

---

## 🌍 Motivation

Code review is one of the most cognitively demanding tasks in software
engineering. Automating it well requires:

- Syntactic understanding (parsing code correctly)
- Semantic reasoning (understanding *what* the code does)
- Domain knowledge (security, algorithms, design patterns)
- Communication (explaining issues clearly)

This environment provides a structured benchmark and training ground
for AI agents to develop all four capabilities — with graded, partial-credit
rewards at every step so RL agents receive a dense learning signal.

---

## 🗂️ Task Suite

| # | Name | Difficulty | What the agent must do |
|---|------|-----------|------------------------|
| 1 | `syntax_error` | Easy | Spot a missing colon in a function signature |
| 2 | `logic_error` | Medium | Fix an inverted boolean condition (`== 1` → `== 0`) |
| 3 | `security_issue` | Medium | Identify SQL injection + hardcoded credentials |
| 4 | `performance` | Hard | Replace O(n²) nested loop with O(n) set-based solution |
| 5 | `code_smell` | Hard | Refactor a god-function violating Single Responsibility Principle |

Difficulty progression: **Easy → Medium → Medium → Hard → Hard**

---

## 📐 Observation Space

```python
class CodeReviewObservation(Observation):
    task: str        # Natural-language description of what to review
    code: str        # Python snippet to analyse
    task_name: str   # Slug identifier for the current task
    reward: float    # Score from the most recent step (0.0–1.0)
    done: bool       # True when episode has ended
    metadata: dict   # difficulty, step count, max_steps, hints
```

## 🎮 Action Space

```python
class CodeReviewAction(Action):
    response: str    # Agent's free-text code review (identify + explain + fix)
```

---

## 🏆 Reward Function

Each grader returns a float in **[0.0, 1.0]** using tiered keyword scoring:

| Score band | Meaning |
|-----------|---------|
| 0.85–0.95 | Correct fix + clear explanation (or uses correct code pattern) |
| 0.55–0.75 | Identifies the issue but fix is incomplete |
| 0.20–0.40 | Mentions the problem area without concrete solution |
| 0.05–0.10 | Off-topic, empty, or trivially short response |

**Reward shaping extras:**
- ✅ **Early bonus** `+0.05` if agent scores ≥ 0.85 before the final step
- ⚠️ **Trivial penalty** `-0.05` for responses shorter than 20 characters

This keeps the reward signal **dense** across the full trajectory —
RL agents receive gradient at every step, not just at episode end.

---

## 🔄 Environment API

```python
from server.code_review_env_environment import CodeReviewEnvironment
from models import CodeReviewAction

env = CodeReviewEnvironment()

obs = env.reset()          # returns CodeReviewObservation
print(obs.task)            # "Identify the syntax error..."
print(obs.code)            # code snippet

result = env.step(CodeReviewAction(response="The colon is missing after def add(a,b)..."))
print(result.reward)       # e.g. 0.92
print(result.done)         # True/False

state = env.state          # episode_id, step_count
```

---

## 🚀 Setup & Usage

### Option A — Docker (recommended)

```bash
docker build -t code-review-env .
docker run -p 8000:8000 \
  -e HF_TOKEN=your_key \
  -e MODEL_NAME=Qwen/Qwen2.5-72B-Instruct \
  code-review-env
```

### Option B — Local

```bash
pip install -r requirements.txt
pip install -e .
python -m server.app
```

### Run the inference baseline

```bash
export HF_TOKEN=your_key
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
python inference.py
```

---

## 📊 Baseline Scores

Measured with `Qwen/Qwen2.5-72B-Instruct` via HF Inference Router:

| Task | Difficulty | Score |
|------|-----------|-------|
| `syntax_error` | Easy | ~0.92 |
| `logic_error` | Medium | ~0.90 |
| `security_issue` | Medium | ~0.65 |
| `performance` | Hard | ~0.60 |
| `code_smell` | Hard | ~0.32 |
| **Average** | — | **~0.68** |

The score distribution confirms meaningful difficulty progression:
frontier models handle easy/medium tasks well but genuinely struggle
with the hard design-pattern tasks.

---

## 📁 Project Structure

```
code-review-env/
├── inference.py                         # Baseline inference script
├── models.py                            # Pydantic Action / Observation models
├── openenv.yaml                         # OpenEnv spec metadata + task list
├── Dockerfile                           # Container definition
├── requirements.txt
├── pyproject.toml
└── server/
    ├── app.py                           # FastAPI app (OpenEnv HTTP server)
    └── code_review_env_environment.py   # Environment logic + graders
```

---

## 🔬 Why This Environment Is Useful

1. **Real task** — Code review happens millions of times per day in industry.
2. **Diverse skills** — 5 tasks cover syntax, logic, security, performance, and design.
3. **Dense rewards** — Partial credit at every step enables RL training, not just eval.
4. **Deterministic graders** — Reproducible scores across runs.
5. **Genuine difficulty spread** — Easy tasks are reliably solved; hard tasks challenge GPT-4-class models.
