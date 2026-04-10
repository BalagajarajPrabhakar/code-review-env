# server/code_review_env_environment.py
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from models import CodeReviewAction, CodeReviewObservation

# Direct import - avoid relative import issues during validation
try:
    from .tasks import TASKS
except ImportError:
    # Fallback for validator
    from tasks import TASKS

class CodeReviewEnvironment(Environment):
    tasks = TASKS   # ← This line is critical for Phase 2

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
                "difficulty": self.current.get("difficulty", "medium"),
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
