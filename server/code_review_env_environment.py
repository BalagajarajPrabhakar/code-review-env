# server/code_review_env_environment.py
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from models import CodeReviewAction, CodeReviewObservation


class CodeReviewEnvironment(Environment):

    # Tasks defined as class attribute — validator uses this list
    tasks = [
        {
            "name": "syntax",
            "task": "Identify the syntax error in the function below and provide the corrected code.",
            "code": "def add(a,b)\n    return a+b",
            "grader": lambda r: max(0.05, min(
                0.9 if any(k in r.lower() for k in ["def add(a,b):", "missing colon", "syntax error", ":"]) else
                0.5 if "fix" in r.lower() else 0.1,
                0.95)),
            "difficulty": "easy",
        },
        {
            "name": "logic",
            "task": "Identify and fix the logical error in the function below.",
            "code": "def is_even(n):\n    return n % 2 == 1",
            "grader": lambda r: max(0.05, min(
                0.9 if any(k in r.lower() for k in ["== 0", "n % 2 == 0", "should be 0"]) else
                0.6 if any(k in r.lower() for k in ["even", "odd", "logic", "wrong"]) else 0.1,
                0.95)),
            "difficulty": "medium",
        },
        {
            "name": "performance",
            "task": "Optimize the following inefficient Python loop for better performance and readability.",
            "code": "result = []\nfor i in range(len(arr)):\n    result.append(arr[i] * 2)",
            "grader": lambda r: max(0.05, min(
                0.9 if any(k in r.lower() for k in ["list comprehension", "[x * 2 for", "[item * 2"]) else
                0.7 if any(k in r.lower() for k in ["comprehension", "enumerate", "map("]) else
                0.4 if any(k in r.lower() for k in ["for x in arr", "for item in arr"]) else 0.1,
                0.95)),
            "difficulty": "hard",
        },
    ]

    def __init__(self):
        self.max_steps = 3
        self._reset_count = 0
        self.current = None
        self._state = State(episode_id=str(uuid4()), step_count=0)

    def reset(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.current = self.tasks[self._reset_count % 3]
        self._reset_count += 1

        return CodeReviewObservation(
            task=self.current["task"],
            code=self.current["code"],
            task_name=self.current["name"],
            done=False,
            reward=0.0,
            metadata={
                "has_grader": True,
                "total_tasks": 3,
                "difficulty": self.current["difficulty"],
            },
        )

    def step(self, action: CodeReviewAction):
        self._state.step_count += 1
        done = self._state.step_count >= self.max_steps
        reward = self.current["grader"](action.response)

        return CodeReviewObservation(
            task=self.current["task"],
            code="Completed" if done else self.current["code"],
            task_name=self.current["name"],
            done=done,
            reward=reward,
            metadata={
                "has_grader": True,
                "total_tasks": 3,
                "difficulty": self.current["difficulty"],
                "step": self._state.step_count,
            },
        )

    @property
    def state(self):
        return self._state
