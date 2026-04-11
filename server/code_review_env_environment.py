# server/code_review_env_environment.py
"""
Code Review Environment — OpenEnv implementation.
Simulates real-world pull-request code review across 5 tasks:
  easy      : syntax_error     — missing colon
  medium    : logic_error      — wrong comparison operator
  medium    : security_issue   — hardcoded secret / SQL injection
  hard      : performance      — O(n²) → O(n) or comprehension
  hard      : code_smell       — god function, no separation of concerns
Reward shaping
--------------
Each grader returns a float in [0.0, 1.0]:
  0.85–0.95  : correct fix + clear explanation
  0.55–0.75  : partially correct (identified issue but fix incomplete)
  0.20–0.40  : identified the issue but no fix
  0.05–0.10  : off-topic or empty response
Partial credit ensures the reward signal is dense (not sparse),
giving RL agents meaningful gradient across the full trajectory.
"""

import re
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from models import CodeReviewAction, CodeReviewObservation


# ── GRADER HELPERS ─────────────────────────────────────────────────────────────

def _score(response: str, high_kws, mid_kws, low_kws=None):
    """
    Generic keyword-tier scorer.
    high_kws → 0.90   mid_kws → 0.60   low_kws → 0.30   else → 0.07
    """
    r = response.lower()
    if any(k in r for k in high_kws):
        return 0.90
    if any(k in r for k in mid_kws):
        return 0.60
    if low_kws and any(k in r for k in low_kws):
        return 0.30
    return 0.07


def _syntax_grader(response: str) -> float:
    """
    Task: fix `def add(a,b)\\n    return a+b`  (missing colon after signature)
    High  : response contains the fixed signature with colon
    Mid   : correctly names the issue (syntax / colon / missing)
    Low   : says 'fix' or 'error' without detail
    """
    r = response.lower()
    # Highest reward: actual corrected code present
    if re.search(r"def add\s*\(a\s*,\s*b\)\s*:", response):
        return 0.92
    return _score(response,
                  high_kws=["def add(a,b):", "add(a, b):", "missing colon", "colon after"],
                  mid_kws=["syntax error", "syntax", "colon", "invalid syntax"],
                  low_kws=["fix", "error", "wrong"])


def _logic_grader(response: str) -> float:
    """
    Task: fix `return n % 2 == 1`  (should be == 0 for is_even)
    High  : correct fix present
    Mid   : correctly identifies the logical inversion
    Low   : mentions even/odd but misses the operator
    """
    r = response.lower()
    if re.search(r"n\s*%\s*2\s*==\s*0", response):
        return 0.92
    return _score(response,
                  high_kws=["== 0", "% 2 == 0", "should return true when", "returns true for odd"],
                  mid_kws=["logic error", "wrong condition", "inverted", "incorrect comparison"],
                  low_kws=["even", "odd", "modulo", "remainder"])


def _security_grader(response: str) -> float:
    """
    Task: spot SQL injection + hardcoded password.
    Code:
        password = "admin123"
        query = "SELECT * FROM users WHERE name = '" + username + "'"
    High  : mentions parameterised query / prepared statement + secret mgmt
    Mid   : identifies SQL injection OR hardcoded secret
    Low   : says 'security' without specifics
    """
    r = response.lower()
    has_sqli = any(k in r for k in ["sql injection", "parameterized", "parameterised",
                                     "prepared statement", "placeholder", "cursor.execute"])
    has_secret = any(k in r for k in ["hardcoded", "hard-coded", "environment variable",
                                       "secret", "os.environ", "vault"])
    if has_sqli and has_secret:
        return 0.93
    if has_sqli or has_secret:
        return 0.65
    if any(k in r for k in ["security", "vulnerability", "unsafe", "injection"]):
        return 0.30
    return 0.07


def _performance_grader(response: str) -> float:
    """
    Task: optimise nested loop (O(n²) duplicate check).
    Code:
        def has_duplicates(lst):
            for i in range(len(lst)):
                for j in range(len(lst)):
                    if i != j and lst[i] == lst[j]:
                        return True
            return False
    High  : suggests set / len(set(lst)) != len(lst)
    Mid   : mentions time complexity / O(n²) → O(n)
    Low   : mentions loop or performance without concrete fix
    """
    r = response.lower()
    if re.search(r"len\s*\(\s*set\s*\(", response) or "set(lst)" in r or "set(" in r:
        return 0.92
    return _score(response,
                  high_kws=["o(n)", "linear time", "use a set", "hash set", "seen = set"],
                  mid_kws=["o(n²)", "o(n^2)", "nested loop", "quadratic", "time complexity"],
                  low_kws=["performance", "optimize", "optimise", "slow", "inefficient"])


def _code_smell_grader(response: str) -> float:
    """
    Task: refactor a 'god function' that does input validation,
    DB query, email sending, and logging all in one 60-line function.
    High  : mentions SRP / single responsibility + suggests split/extract
    Mid   : identifies it does too many things / separation of concerns
    Low   : says 'refactor' or 'clean' without reasoning
    """
    r = response.lower()
    has_srp = any(k in r for k in ["single responsibility", "srp", "separation of concerns",
                                    "separate function", "extract function", "decompose"])
    has_smell = any(k in r for k in ["god function", "too many responsibilities",
                                      "does too much", "violates", "multiple concerns"])
    if has_srp and has_smell:
        return 0.92
    if has_srp or has_smell:
        return 0.62
    if any(k in r for k in ["refactor", "clean", "readable", "maintainable", "split"]):
        return 0.32
    return 0.07


# ── TASK DEFINITIONS ───────────────────────────────────────────────────────────

TASKS = [
    {
        "name": "syntax_error",
        "difficulty": "easy",
        "task": (
            "Review the Python function below. "
            "Identify the syntax error, explain why it is wrong, "
            "and provide the corrected code."
        ),
        "code": (
            "def add(a,b)\n"
            "    return a+b"
        ),
        "grader": _syntax_grader,
        "ideal_fix": "def add(a, b):\n    return a + b",
    },
    {
        "name": "logic_error",
        "difficulty": "medium",
        "task": (
            "Review the Python function below. "
            "Identify the logical error, explain the correct behaviour, "
            "and provide the corrected code."
        ),
        "code": (
            "def is_even(n):\n"
            "    return n % 2 == 1"
        ),
        "grader": _logic_grader,
        "ideal_fix": "def is_even(n):\n    return n % 2 == 0",
    },
    {
        "name": "security_issue",
        "difficulty": "medium",
        "task": (
            "Review the Python snippet below for security vulnerabilities. "
            "Identify ALL issues, explain the risks, "
            "and provide a secure rewrite."
        ),
        "code": (
            "password = \"admin123\"\n"
            "def get_user(username):\n"
            "    query = \"SELECT * FROM users WHERE name = '\" + username + \"'\"\n"
            "    return db.execute(query)"
        ),
        "grader": _security_grader,
        "ideal_fix": (
            "Use parameterised queries and load secrets from environment variables."
        ),
    },
    {
        "name": "performance",
        "difficulty": "hard",
        "task": (
            "Review the Python function below. "
            "Identify the performance problem, explain its time complexity, "
            "and provide an optimised version."
        ),
        "code": (
            "def has_duplicates(lst):\n"
            "    for i in range(len(lst)):\n"
            "        for j in range(len(lst)):\n"
            "            if i != j and lst[i] == lst[j]:\n"
            "                return True\n"
            "    return False"
        ),
        "grader": _performance_grader,
        "ideal_fix": "def has_duplicates(lst):\n    return len(set(lst)) != len(lst)",
    },
    {
        "name": "code_smell",
        "difficulty": "hard",
        "task": (
            "Review the function below. "
            "Identify code-smell issues (design / maintainability), "
            "explain which principles are violated, "
            "and propose a refactored structure."
        ),
        "code": (
            "def process_user_request(user_id, email, data):\n"
            "    # validate\n"
            "    if not user_id or not email:\n"
            "        raise ValueError('missing fields')\n"
            "    if '@' not in email:\n"
            "        raise ValueError('bad email')\n"
            "    # query db\n"
            "    user = db.query(f'SELECT * FROM users WHERE id={user_id}')\n"
            "    if not user:\n"
            "        raise LookupError('user not found')\n"
            "    # update record\n"
            "    db.execute(f'UPDATE users SET data={data} WHERE id={user_id}')\n"
            "    # send email\n"
            "    smtp.send(email, 'Update successful', f'Hi {user.name}, done.')\n"
            "    # log\n"
            "    logger.info(f'processed {user_id}')\n"
            "    return True"
        ),
        "grader": _code_smell_grader,
        "ideal_fix": (
            "Split into validate_user(), fetch_user(), update_user(), "
            "notify_user(), log_action() — one responsibility each."
        ),
    },
]


# ── ENVIRONMENT ────────────────────────────────────────────────────────────────

class CodeReviewEnvironment(Environment):
    """
    OpenEnv environment for AI-driven code review.
    Episode flow
    ------------
    reset()  →  loads the next task in round-robin order
    step()   →  agent submits a review; grader scores it (0.0–1.0)
                episode ends after max_steps OR when agent scores ≥ 0.85
    Reward shaping
    --------------
    - Partial credit at every step (not sparse end-of-episode only)
    - Bonus +0.05 for high-quality reviews (score ≥ 0.85) submitted in < max_steps
    - Penalty -0.05 for empty/trivial responses (< 20 chars)
    """

    tasks = TASKS  # validator reads this attribute

    def __init__(self):
        self.max_steps = 3
        self._reset_count = 0
        self.current = None
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._best_reward = 0.0

    def reset(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._best_reward = 0.0
        self.current = TASKS[self._reset_count % len(TASKS)]
        self._reset_count += 1

        return CodeReviewObservation(
            task=self.current["task"],
            code=self.current["code"],
            task_name=self.current["name"],
            reward=0.0,
            done=False,
            metadata={
                "has_grader": True,
                "total_tasks": len(TASKS),
                "difficulty": self.current["difficulty"],
                "step": 0,
                "max_steps": self.max_steps,
                "hint": f"Difficulty: {self.current['difficulty']}",
            },
        )

    def step(self, action: CodeReviewAction):
        self._state.step_count += 1
        step = self._state.step_count

        # Score the agent's review
        raw_reward = self.current["grader"](action.response)

        # Reward shaping
        if len(action.response.strip()) < 20:
            raw_reward = max(0.0, raw_reward - 0.05)   # penalty: trivial response
        if raw_reward >= 0.85 and step < self.max_steps:
            raw_reward = min(0.95, raw_reward + 0.05)  # bonus: early high-quality fix

        self._best_reward = max(self._best_reward, raw_reward)
        done = (step >= self.max_steps) or (raw_reward >= 0.85)

        return CodeReviewObservation(
            task=self.current["task"],
            code="✓ Review complete." if done else self.current["code"],
            task_name=self.current["name"],
            reward=raw_reward,
            done=done,
            metadata={
                "has_grader": True,
                "total_tasks": len(TASKS),
                "difficulty": self.current["difficulty"],
                "step": step,
                "max_steps": self.max_steps,
                "best_reward_this_episode": self._best_reward,
                "ideal_fix_hint": self.current["ideal_fix"] if done else "",
            },
        )

    @property
    def state(self):
        return self._state
