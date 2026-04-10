# server/code_review_env_environment.py
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from models import CodeReviewAction, CodeReviewObservation


# ====================== GRADERS ======================
def grader_syntax(response: str) -> float:
    response = response.lower().strip()
    score = 0.15
    if any(k in response for k in [":", "colon", "syntax", "indent", "def "]):
        score += 0.35
    if any(k in response for k in ["because", "error", "missing", "fix", "should be"]):
        score += 0.30
    if len(response) > 50:
        score += 0.15
    return max(0.05, min(score, 0.95))


def grader_logic(response: str) -> float:
    response = response.lower().strip()
    score = 0.15
    if any(k in response for k in ["% 2", "== 0", "even", "modulo", "remainder"]):
        score += 0.40
    if any(k in response for k in ["because", "logic", "condition", "wrong", "should return"]):
        score += 0.30
    if len(response) > 50:
        score += 0.10
    return max(0.05, min(score, 0.95))


def grader_performance(response: str) -> float:
    response = response.lower().strip()
    score = 0.15
    if any(k in response for k in ["enumerate", "for x in", "comprehension", "range(len"]):
        score += 0.45
    if any(k in response for k in ["efficient", "performance", "optimize", "faster"]):
        score += 0.25
    if len(response) > 55:
        score += 0.10
    return max(0.05, min(score, 0.95))


# ====================== TASKS ======================
TASKS = [
    {
        "name": "syntax",
        "task": "Identify syntax error and fix it.",
        "code": "def add(a,b)\n return a+b",
        "grader": grader_syntax,
        "difficulty": "easy"
    },
    {
        "name": "logic",
        "task": "Fix logical error.",
        "code": "def is_even(n): return n % 2 == 1",
        "grader": grader_logic,
        "difficulty": "medium"
    },
    {
        "name": "performance",
        "task": "Optimize performance.",
        "code": "for i in range(len(arr)): print(arr[i])",
        "grader": grader_performance,
        "difficulty": "hard"
    }
]


# ====================== ENVIRONMENT ======================
class CodeReviewEnvironment(Environment):
    tasks = TASKS   # ← This is what the validator looks for

    def __init__(self):
        self.max_steps = 3
        self._reset_count = 0
        self.current = None
        self._state = State(episode_id=str(uuid4()), step_count=0)

    def reset(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        idx = self._reset_count % len(self.tasks)
        self.current = self.tasks[idx]
        self._reset_count += 1

        return CodeReviewObservation(
            task=self.current["task"],
            code=self.current["code"],
            done=False,
            reward=0.1,
            metadata={
                "task_name": self.current["name"],
                "difficulty": self.current["difficulty"],
                "grader_name": f"{self.current['name']}_grader",
                "has_grader": True,
                "total_tasks": len(self.tasks)
            }
        )

    def step(self, action: CodeReviewAction):
        self._state.step_count += 1
        done = self._state.step_count >= self.max_steps
        reward = self.current["grader"](action.response)

        return CodeReviewObservation(
            task=self.current["task"],
            code="Task completed" if done else self.current["code"],
            done=done,
            reward=reward,
            metadata={
                "step": self._state.step_count,
                "task_name": self.current["name"],
                "grader_name": f"{self.current['name']}_grader",
                "has_grader": True,
                "total_tasks": len(self.tasks)
            }
        )

    @property
    def state(self):
        return self._state
