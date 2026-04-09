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
        "id": 1,
        "task": "You are reviewing a junior developer's pull request. Identify the syntax error and suggest a fix.",
        "code": "def add(a,b)\n return a+b",
        "bug": "missing colon",
        "fix": ":"
    },
    {
        "id": 2,
        "task": "You are performing a backend code review. Identify the logical error and correct it.",
        "code": "def is_even(n): return n % 2 == 1",
        "bug": "wrong condition",
        "fix": "== 0"
    },
    {
        "id": 3,
        "task": "You are optimizing production code. Improve performance and suggest better implementation.",
        "code": "for i in range(len(arr)): print(arr[i])",
        "bug": "inefficient",
        "fix": "for x in arr"
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
        # Step count
        self._state.step_count += 1

        # Initialize done
        done = False

        # Get agent response
        response = action.response.lower()

        reward = 0.0

        #  Bug detection
        if any(word in response for word in self.current["bug"].split()):
            reward += 0.3

        #  Fix detection
        if any(word in response for word in self.current["fix"].split()):
            reward += 0.3

        #  Explanation
        if "because" in response or "reason" in response:
            reward += 0.2

        #  Understanding
        if "error" in response or "issue" in response:
            reward += 0.1

        #  Quality bonus
        if len(response) > 30:
            reward += 0.1


        #  VERY IMPORTANT (Phase 2 fix)
        if reward <= 0:
            reward = 0.1   #  avoid 0

        elif reward >= 1:
            reward = 0.9   #  avoid 1

        #  Success condition
        if reward >= 0.8:
            done = True

        #  Max step condition
        if self._state.step_count >= self.max_steps:
            done = True

        return CodeReviewObservation(
            code="Completed" if done else self.current["code"],
            task=self.current["task"],
            done=done,
            reward=reward,
            metadata={
    "task_id": self.current["id"],
    "bug_detected": self.current["bug"] in response,
    "fix_suggested": self.current["fix"] in response,
    "step": self._state.step_count
}
        )

    @property
    def state(self):
        return self._state
