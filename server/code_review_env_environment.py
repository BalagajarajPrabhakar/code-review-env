# server/code_review_env_environment.py
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from models import CodeReviewAction, CodeReviewObservation


# === GRADERS (defined directly here) ===
def grader_syntax(response: str) -> float:
    r = response.lower().strip()
    score = 0.15
    if any(k in r for k in [":", "syntax", "indent", "def "]):
        score += 0.35
    if any(k in r for k in ["because", "error", "fix"]):
        score += 0.30
    if len(r) > 40:
        score += 0.15
    return max(0.05, min(score, 0.95))


def grader_logic(response: str) -> float:
    r = response.lower().strip()
    score = 0.15
    if any(k in r for k in ["% 2", "== 0", "even", "modulo"]):
        score += 0.40
    if any(k in r for k in ["because", "logic", "condition"]):
        score += 0.30
    if len(r) > 40:
        score += 0.10
    return max(0.05, min(score, 0.95))


def grader_performance(response: str) -> float:
    r = response.lower().strip()
    score = 0.15
    if any(k in r for k in ["enumerate", "for x in", "comprehension"]):
        score += 0.45
    if any(k in r for k in ["efficient", "performance", "optimize"]):
        score += 0.25
    if len(r) > 45:
        score += 0.10
    return max(0.05, min(score, 0.95))


# === TASKS (defined directly here) ===
TASKS = [
    {"name": "syntax", "task": "Identify syntax error and fix it.", "code": "def add(a,b)\n return a+b", "grader": grader_syntax, "difficulty": "easy"},
    {"name": "logic", "task": "Fix logical error.", "code": "def is_even(n): return n % 2 == 1", "grader": grader_logic, "difficulty": "medium"},
    {"name": "performance", "task": "Optimize performance.", "code": "for i in range(len(arr)): print(arr[i])", "grader": grader_performance, "difficulty": "hard"}
]


class CodeReviewEnvironment(Environment):
    tasks = TASKS   # ← This must be a class attribute at this level

    def __init__(self):
        self.max_steps = 3
        self._reset_count = 0
        self.current = None
        self._state = State(episode_id=str(uuid4()), step_count=0)

    def reset(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.current = self.tasks[self._reset_count % len(self.tasks)]
        self._reset_count += 1

        return CodeReviewObservation(
            task=self.current["task"],
            code=self.current["code"],
            done=False,
            reward=0.1,
            metadata={"has_grader": True, "total_tasks": len(self.tasks)}
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
            metadata={"has_grader": True, "total_tasks": len(self.tasks)}
        )

    @property
    def state(self):
        return self._state
