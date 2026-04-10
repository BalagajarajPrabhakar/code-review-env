# server/graders.py
def grader_syntax(response: str) -> float:
    response = response.lower()
    score = 0.2  # start with a small base > 0.0

    if any(kw in response for kw in [":", "colon", "syntax", "indent", "def "]):
        score += 0.3
    if any(kw in response for kw in ["because", "error", "missing", "fix", "should be"]):
        score += 0.25
    if len(response.strip()) > 40:
        score += 0.15

    # Force strictly between 0.0 and 1.0
    score = max(0.05, min(score, 0.95))
    return round(score, 4)   # clean float


def grader_logic(response: str) -> float:
    response = response.lower()
    score = 0.2

    if any(kw in response for kw in ["% 2", "== 0", "even", "modulo", "remainder"]):
        score += 0.35
    if any(kw in response for kw in ["because", "logic", "condition", "wrong", "should return"]):
        score += 0.25
    if len(response.strip()) > 40:
        score += 0.15

    score = max(0.05, min(score, 0.95))
    return round(score, 4)


def grader_performance(response: str) -> float:
    response = response.lower()
    score = 0.2

    if any(kw in response for kw in ["enumerate", "for x in", "list comp", "comprehension", "range(len"]):
        score += 0.4
    if any(kw in response for kw in ["efficient", "performance", "optimize", "better", "faster"]):
        score += 0.25
    if len(response.strip()) > 45:
        score += 0.1

    score = max(0.05, min(score, 0.95))
    return round(score, 4)
