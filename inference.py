"""
inference.py — Code Review Environment Baseline
================================================
Runs all 5 tasks against the configured LLM and emits strict
[START] / [STEP] / [END] logs required by the OpenEnv validator.
Environment variables (all required at runtime):
  HF_TOKEN      / API_KEY   — API key
  API_BASE_URL              — LLM endpoint  (default: HF router)
  MODEL_NAME                — model id      (default: Qwen2.5-72B-Instruct)
"""

import asyncio
import os
from typing import List

from openai import OpenAI

from server.code_review_env_environment import CodeReviewEnvironment, TASKS
from models import CodeReviewAction

# ── ENV VARIABLES ──────────────────────────────────────────────────────────────
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

BENCHMARK = "code_review_env"
MAX_STEPS = 3
SUCCESS_THRESHOLD = 0.70

SYSTEM_PROMPT = (
    "You are a senior software engineer conducting a pull-request code review. "
    "For every snippet you receive:\n"
    "  1. Identify the specific bug, error, or issue.\n"
    "  2. Explain clearly why it is wrong.\n"
    "  3. Provide the corrected / improved code.\n"
    "Be concise but precise. Do not add unnecessary preamble."
)


# ── STRICT LOG FORMAT ──────────────────────────────────────────────────────────
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error) -> None:
    action_clean = action.replace("\n", " ").replace("\r", "")[:120]
    error_val = error if error else "null"
    print(
        f"[STEP] step={step} action={action_clean} "
        f"reward={reward:.2f} done={str(done).lower()} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ── LLM CALL ──────────────────────────────────────────────────────────────────
def call_model(client: OpenAI, task_desc: str, code: str) -> str:
    user_prompt = f"Task: {task_desc}\n\nCode to review:\n```python\n{code}\n```"
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=400,
            temperature=0.3,   # lower temp → more deterministic / reproducible
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        print(f"[DEBUG] LLM call failed: {exc}", flush=True)
        # Deterministic fallback so scoring always produces a value
        return f"There is an issue in the code. Please review and fix it. Error details: {str(exc)[:80]}"


# ── SINGLE TASK EPISODE ────────────────────────────────────────────────────────
def run_task(client: OpenAI, env: CodeReviewEnvironment, task_index: int) -> float:
    task_name = TASKS[task_index]["name"]
    log_start(task_name, BENCHMARK, MODEL_NAME)

    # Point the env at the correct task
    env._reset_count = task_index
    obs = env.reset()

    rewards: List[float] = []
    steps_taken = 0

    for step in range(1, MAX_STEPS + 1):
        action_text = call_model(client, obs.task, obs.code)
        result = env.step(CodeReviewAction(response=action_text))

        obs = result
        reward = result.reward
        done = result.done

        rewards.append(reward)
        steps_taken = step
        log_step(step, action_text, reward, done, None)

        if done:
            break

    score = sum(rewards) / len(rewards) if rewards else 0.0
    score = round(max(0.0, min(score, 1.0)), 3)
    success = score >= SUCCESS_THRESHOLD

    log_end(success, steps_taken, score, rewards)
    return score


# ── MAIN ───────────────────────────────────────────────────────────────────────
async def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = CodeReviewEnvironment()

    all_scores: List[float] = []
    for i in range(len(TASKS)):
        score = run_task(client, env, i)
        all_scores.append(score)

    avg = sum(all_scores) / len(all_scores)
    difficulties = [t["difficulty"] for t in TASKS]
    names = [t["name"] for t in TASKS]

    print(
        f"\n[SUMMARY] tasks={len(TASKS)} avg_score={avg:.3f} "
        f"scores={','.join(f'{s:.3f}' for s in all_scores)} "
        f"tasks={','.join(names)} "
        f"difficulties={','.join(difficulties)}",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
