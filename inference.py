import asyncio
import os
from typing import List

from openai import OpenAI
from server.code_review_env_environment import CodeReviewEnvironment
from models import CodeReviewAction

#  ENV VARIABLES (MANDATORY)
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

#  CONFIG
TASK_NAME = "code_review"
BENCHMARK = "code_review_env"
MAX_STEPS = 3
SUCCESS_THRESHOLD = 0.7


#  LOGGING FUNCTIONS (STRICT FORMAT)
def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}")


def log_step(step, action, reward, done, error):
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error}"
    )


def log_end(success, steps, score, rewards):
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}"
    )


#  MODEL CALL
def get_model_response(client, prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[DEBUG] Model request failed: {e}", flush=True)
        return "There is a bug in the code. Fix it."


#  MAIN EXECUTION
async def main():
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    env = CodeReviewEnvironment()
    rewards: List[float] = []

    steps_taken = 0
    success = False
    score = 0.0

    log_start(TASK_NAME, BENCHMARK, MODEL_NAME)

    try:
        
        obs = env.reset()

        for step in range(1, MAX_STEPS + 1):

            prompt = f"""
You are a senior software engineer reviewing a pull request.

Task: {obs.task}

Code:
{obs.code}

Instructions:
1. Identify the bug
2. Explain why it is wrong
3. Provide the correct fix
"""

            action_text = get_model_response(client, prompt)

            result = env.step(CodeReviewAction(response=action_text))

            obs = result
            reward = result.reward
            done = result.done
            error = None

            rewards.append(reward)
            steps_taken = step

            log_step(step, action_text, reward, done, error)

            if done:
                break

        #  SCORE CALCULATION
        if len(rewards) > 0:
            score = sum(rewards) / len(rewards)

        score = max(0.0, min(score, 1.0))
        success = score >= SUCCESS_THRESHOLD

    finally:
        log_end(success, steps_taken, score, rewards)


if __name__ == "__main__":
    asyncio.run(main())


