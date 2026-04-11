"""
inference.py - Code Review Environment Baseline
Runs all 3 tasks (syntax, logic, performance) separately.
Emits strict [START] / [STEP] / [END] log format required by the validator.
"""

import asyncio
import os
from typing import List

from openai import OpenAI
from server.code_review_env_environment import CodeReviewEnvironment
from models import CodeReviewAction

# ── ENV VARIABLES (MANDATORY) ──────────────────────────────────────────────────
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

# ── CONFIG ──────────────────────────────────────────────────────────────────────
BENCHMARK = "code_review_env"
MAX_STEPS = 3
SUCCESS_THRESHOLD = 0.7

# Task names must match the `name` field in openenv.yaml tasks
TASKS = ["syntax", "logic", "performance"]


# ── LOGGING (STRICT FORMAT — DO NOT CHANGE) ────────────────────────────────────
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    # Sanitise action: strip newlines so the log stays on one line
    action_clean = action.replace("\n", " ").replace("\r", "")[:120]
    print(
        f"[STEP] step={step} action={action_clean} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


# ── LLM CALL ────────────────────────────────────────────────────────────────────
def get_model_response(client: OpenAI, task_desc: str, code: str) -> str:
    prompt = (
        "You are a senior software engineer reviewing a pull request.\n\n"
        f"Task: {task_desc}\n\nCode:\n{code}\n\n"
        "Instructions:\n"
        "1. Identify the bug or issue\n"
        "2. Explain why it is wrong\n"
        "3. Provide the correct fix with code\n"
    )
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[DEBUG] Model request failed: {e}", flush=True)
        return "There is a bug in the code. Fix it."


# ── RUN ONE TASK ────────────────────────────────────────────────────────────────
def run_task(client: OpenAI, env: CodeReviewEnvironment, task_index: int, task_name: str):
    """Run a single task episode and emit START / STEP / END logs."""
    log_start(task_name, BENCHMARK, MODEL_NAME)

    rewards: List[float] = []
    steps_taken = 0

    # Force the environment to load the correct task by resetting to the right index
    # We call reset() and skip ahead to the desired task
    env._reset_count = task_index
    obs = env.reset()

    for step in range(1, MAX_STEPS + 1):
        action_text = get_model_response(client, obs.task, obs.code)
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
    score = max(0.0, min(score, 1.0))
    success = score >= SUCCESS_THRESHOLD

    log_end(success, steps_taken, score, rewards)
    return score


# ── MAIN ────────────────────────────────────────────────────────────────────────
async def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env = CodeReviewEnvironment()

    all_scores = []
    for i, task_name in enumerate(TASKS):
        score = run_task(client, env, i, task_name)
        all_scores.append(score)

    avg = sum(all_scores) / len(all_scores)
    print(f"\n[SUMMARY] tasks={len(TASKS)} avg_score={avg:.3f} scores={','.join(f'{s:.3f}' for s in all_scores)}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
