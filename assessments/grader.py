"""Simple grading module. Keeps logic modular so it can be swapped with an LLM-based grader later."""
from typing import Tuple


def grade_mcq(expected_key: str, selected_key: str, points: float) -> Tuple[float, float]:
    """Return (points_awarded, points_possible) for MCQ."""
    if expected_key is None:
        return 0.0, points
    awarded = points if str(expected_key).strip().lower() == str(selected_key).strip().lower() else 0.0
    return awarded, points


def grade_text(expected_keywords, answer_text: str, points: float) -> Tuple[float, float]:
    """Simple keyword-density grading: fraction of keywords present * points."""
    if not expected_keywords:
        return 0.0, points
    if isinstance(expected_keywords, str):
        keywords = [k.strip().lower() for k in expected_keywords.split(",") if k.strip()]
    else:
        keywords = [str(k).strip().lower() for k in expected_keywords]
    answer = (answer_text or "").lower()
    if not keywords:
        return 0.0, points
    matched = sum(1 for kw in keywords if kw and kw in answer)
    ratio = matched / len(keywords)
    awarded = round(ratio * points, 4)
    return awarded, points


def grade_question(question, answer_obj) -> Tuple[float, float]:
    """Grade a Question instance against an Answer-like object.
    Returns (points_awarded, points_possible).
    """
    qtype = question.question_type
    if qtype == "mcq":
        expected = question.expected_answer
        selected = getattr(answer_obj, "selected_choice", None) or getattr(answer_obj, "answer_text", None)
        # expected may be stored as a string or JSON; normalize
        if isinstance(expected, dict) and "key" in expected:
            expected_key = expected.get("key")
        else:
            expected_key = expected
        return grade_mcq(expected_key, selected, question.points)
    else:
        expected = question.expected_answer
        return grade_text(expected, getattr(answer_obj, "answer_text", ""), question.points)
