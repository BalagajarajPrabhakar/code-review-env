# server/code_review_env_environment.py
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from models import CodeReviewAction, CodeReviewObservation


class CodeReviewEnvironment(Environment):
    
    # Tasks defined directly as class attribute - this is what validator looks for
    tasks = [
        {
            "name": "syntax",
            "task": "Identify syntax error and fix it.",
            "code": "def add(a,b)\n return a+b",
            "grader": lambda response: max(0.05, min(0.8 if any(k in response.lower() for k in [":", "syntax", "fix"]) else 0.1, 0.95)),
            "difficulty": "easy"
        },
        {
            "name": "logic",
            "task": "Fix logical error.",
            "code": "def is_even(n): return n % 2 == 1",
            "grader": lambda response: max(0.05, min(0.8 if any(k in response.lower() for k in ["even", "% 2", "== 0"]) else 0.1, 0.95)),
            "difficulty": "medium"
        },
        {
            "name": "performance",
            "task": "Optimize performance.",
            "code": "for i in range(len(arr)): print(arr[i])",
            "grader": lambda response: max(0.05, min(0.8 if any(k in response.lower() for k in ["enumerate", "for x in", "comprehension"]) else 0.1, 0.95)),
            "difficulty": "hard"
        }
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
            done=False,
            reward=0.1,
            metadata={"has_grader": True, "total_tasks": 3}
        )

    def step(self, action: CodeReviewAction):
        self._state.step_count += 1
        done = self._state.step_count >= self.max_steps
        reward = self.current["grader"](action.response)

        return CodeReviewObservation(
            task=self.current["task"],
            code="Completed" if done else self.current["code"],
            done=done,
            reward=reward,
            metadata={"has_grader": True, "total_tasks": 3}
        )

    @property
    def state(self):
        return self._state
