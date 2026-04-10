# graders.py
def grader_syntax(response: str) -> float:
    response = response.lower()
    score = 0.0
    if any(kw in response for kw in [":", "colon", "syntax"]):
        score += 0.5
    if any(kw in response for kw in ["because", "error", "fix"]):
        score += 0.3
    if len(response) > 30:
        score += 0.2
    return max(0.0, min(score, 1.0))   # MUST be 0.0–1.0


def grader_logic(response: str) -> float:
    response = response.lower()
    score = 0.0
    if any(kw in response for kw in ["==", "even", "mod", "% 2"]):
        score += 0.5
    if any(kw in response for kw in ["because", "logic", "condition"]):
        score += 0.3
    if len(response) > 30:
        score += 0.2
    return max(0.0, min(score, 1.0))


def grader_performance(response: str) -> float:
    response = response.lower()
    score = 0.0
    if any(kw in response for kw in ["enumerate", "for x in", "range(len", "comprehension"]):
        score += 0.6
    if any(kw in response for kw in ["efficient", "performance", "better", "optimize"]):
        score += 0.3
    if len(response) > 40:
        score += 0.1
    return max(0.0, min(score, 1.0))