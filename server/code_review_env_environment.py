import random
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State
from uuid import uuid4

from models import CodeReviewAction, CodeReviewObservation

def simple_grader(response: str, expected_keywords: list, explanation_keywords: list):
    response = response.lower()
    score = 0.0

    # keyword match
    if any(word in response for word in expected_keywords):
        score += 0.5

    # explanation match
    if any(word in response for word in explanation_keywords):
        score += 0.3

    # bonus
    if len(response) > 30:
        score += 0.1

    # clamp STRICT (0,1)
    score = max(0.1, min(score, 0.9))

    return score

def grader_syntax(response: str) -> float:
    return simple_grader(
        response,
        expected_keywords=["colon", ":"],
        explanation_keywords=["because", "syntax"]
    )


def grader_logic(response: str) -> float:
    return simple_grader(
        response,
        expected_keywords=["== 0", "even"],
        explanation_keywords=["because", "logic"]
    )


def grader_performance(response: str) -> float:
    return simple_grader(
        response,
        expected_keywords=["for x in arr"],
        explanation_keywords=["efficient", "performance"]
    )
    
class CodeReviewEnvironment(Environment):

    def __init__(self):
        self.max_steps = 3
        self._state = State(episode_id=str(uuid4()), step_count=0)

        self.tasks = [
    {
        "task": "Identify syntax error and fix it.",
        "code": "def add(a,b)\n return a+b",
        "grader": grader_syntax
    },
    {
        "task": "Fix logical error.",
        "code": "def is_even(n): return n % 2 == 1",
        "grader": grader_logic
    },
    {
        "task": "Optimize performance.",
        "code": "for i in range(len(arr)): print(arr[i])",
        "grader": grader_performance
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
            reward=0.1,  # NOT 0 (important)
            metadata={
            "has_grader": True,
            "grader_name": self.current["grader"].__name__,
            "total_tasks": len(self.tasks)
    }
)

    def step(self, action: CodeReviewAction):

        self._state.step_count += 1
        done = self._state.step_count >= self.max_steps

        response = action.response

        #  REAL GRADER
        reward = self.current["grader"](response)

        return CodeReviewObservation(
            code="Completed" if done else self.current["code"],
            task=self.current["task"],
            done=done,
            reward=reward,
            metadata={
    "step": self._state.step_count,
    "grader_used": self.current["grader"].__name__,
    "has_grader": True,
    "score_range": "(0,1)"
}
        )

    @property
    def state(self):
        return self._state
