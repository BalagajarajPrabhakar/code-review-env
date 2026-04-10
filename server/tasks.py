# tasks.py
from .graders import grader_syntax, grader_logic, grader_performance

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

__all__ = ["TASKS"]