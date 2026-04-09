import random
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State
from uuid import uuid4

from models import CodeReviewAction, CodeReviewObservation


class CodeReviewEnvironment(Environment):

    def __init__(self):
        self.max_steps = 3
        self._state = State(episode_id=str(uuid4()), step_count=0)

        self.tasks = [
    {
        "task": "Identify syntax error and fix it.",
        "code": "def add(a,b)\n return a+b",
        "grader": {
            "must_include": ["colon", ":"],
            "explanation": ["because", "syntax"]
        }
    },
    {
        "task": "Fix logical error.",
        "code": "def is_even(n): return n % 2 == 1",
        "grader": {
            "must_include": ["== 0", "even"],
            "explanation": ["because", "logic"]
        }
    },
    {
        "task": "Optimize performance.",
        "code": "for i in range(len(arr)): print(arr[i])",
        "grader": {
            "must_include": ["for x in arr"],
            "explanation": ["efficient", "performance"]
        }
    }
]

        self.current = None
        self._reset_count = 0

    def reset(self):
        # Reset state
        self._state = State(episode_id=str(uuid4()), step_count=0)

        # Deterministic task selection
        self.current = self.tasks[self._reset_count % len(self.tasks)]
        self._reset_count += 1

        return CodeReviewObservation(
            code=self.current["code"],
            task=self.current["task"],
            done=False,
            reward=0.0,
        )

    def step(self, action: CodeReviewAction):

        self._state.step_count += 1
        done = self._state.step_count >= self.max_steps

        response = action.response.lower()
        grader = self.current["grader"]

        reward = 0.0

        #  Keyword match
        matched_keywords = [
            word for word in grader["must_include"]
            if word.lower() in response
        ]

        if matched_keywords:
            reward += 0.5

        #  Explanation match
        matched_explanations = [
            word for word in grader["explanation"]
            if word.lower() in response
        ]

        if matched_explanations:
            reward += 0.3

        #  Bonus
        if len(response) > 30:
            reward += 0.1

        #  Penalty
        if len(response) < 10:
            reward -= 0.2

        if "i don't know" in response:
            reward -= 0.3

        #  CRITICAL (Hackathon Rule)
        reward = max(0.1, min(reward, 0.9))

        return CodeReviewObservation(
            code="Completed" if done else self.current["code"],
            task=self.current["task"],
            done=done,
            reward=reward,
            metadata={
                "matched_keywords": matched_keywords,
                "matched_explanations": matched_explanations,
                "step": self._state.step_count,
                "score_range": "(0,1)"
        }
    )

    @property
    def state(self):
        return self._state
