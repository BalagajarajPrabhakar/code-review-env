# server/graders.py
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
