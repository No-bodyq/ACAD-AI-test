
"""
Enhanced grading module with LLM integration.
Supports multiple grading strategies: mock, LLM-based, or hybrid.
"""
from typing import Tuple, Optional, Dict, Any
from abc import ABC, abstractmethod
import os
from enum import Enum

class GradingStrategy(Enum):
    """Available grading strategies."""
    MOCK = "mock"
    LLM = "llm"
    HYBRID = "hybrid"  # Uses LLM for text, mock for MCQ

class BaseGrader(ABC):
    """Abstract base class for all grading implementations."""
    
    @abstractmethod
    def grade_mcq(self, expected_key: str, selected_key: str, points: float) -> Tuple[float, float, Optional[str]]:
        """Return (points_awarded, points_possible, feedback)."""
        pass
    
    @abstractmethod
    def grade_text(self, question_text: str, expected_answer: Any, student_answer: str, 
                   points: float) -> Tuple[float, float, Optional[str]]:
        """Return (points_awarded, points_possible, feedback)."""
        pass


class MockGrader(BaseGrader):
    """Simple keyword-based grading without LLM."""
    
    def grade_mcq(self, expected_key: str, selected_key: str, points: float) -> Tuple[float, float, Optional[str]]:
        """Grade multiple choice question."""
        if expected_key is None:
            return 0.0, points, None
        
        is_correct = str(expected_key).strip().lower() == str(selected_key).strip().lower()
        awarded = points if is_correct else 0.0
        feedback = "Correct!" if is_correct else f"Incorrect. Expected: {expected_key}"
        
        return awarded, points, feedback
    
    def grade_text(self, question_text: str, expected_answer: Any, student_answer: str, 
                   points: float) -> Tuple[float, float, Optional[str]]:
        """Simple keyword-density grading."""
        if not expected_answer:
            return 0.0, points, "No expected answer provided."
        
        # Parse keywords
        if isinstance(expected_answer, str):
            keywords = [k.strip().lower() for k in expected_answer.split(",") if k.strip()]
        else:
            keywords = [str(k).strip().lower() for k in expected_answer]
        
        answer = (student_answer or "").lower()
        
        if not keywords:
            return 0.0, points, "No keywords to match."
        
        # Calculate keyword matches
        matched = sum(1 for kw in keywords if kw and kw in answer)
        ratio = matched / len(keywords)
        awarded = round(ratio * points, 4)
        
        feedback = f"Matched {matched}/{len(keywords)} keywords. Score: {ratio*100:.1f}%"
        
        return awarded, points, feedback
    

class GeminiGrader(BaseGrader):
    """LLM-based grading using Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        """
        Initialize Gemini grader.
        
        Args:
            api_key: Google API key (defaults to env variable)
            model: Model to use
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Install google-generativeai: pip install google-generativeai")
        
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") 
        if not self.api_key:
            raise ValueError("Google API key not provided")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)
    
    def grade_mcq(self, expected_key: str, selected_key: str, points: float) -> Tuple[float, float, Optional[str]]:
        """MCQ grading (uses simple matching)."""
        mock_grader = MockGrader()
        return mock_grader.grade_mcq(expected_key, selected_key, points)
    
    def grade_text(self, question_text: str, expected_answer: Any, student_answer: str, 
                   points: float) -> Tuple[float, float, Optional[str]]:
        """Gemini-based text grading."""
        if not student_answer or not student_answer.strip():
            return 0.0, points, "No answer provided."
        
        try:
            prompt = self._build_grading_prompt(question_text, expected_answer, student_answer, points)
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 500,
                }
            )
            
            result = response.text
            score, feedback = self._parse_llm_response(result, points)
            
            return score, points, feedback
            
        except Exception as e:
            print(f"Gemini grading failed: {e}. Falling back to keyword matching.")
            mock_grader = MockGrader()
            return mock_grader.grade_text(question_text, expected_answer, student_answer, points)
    
    def _build_grading_prompt(self, question: str, expected: Any, student: str, points: float) -> str:
        """Build the grading prompt for Gemini."""
        return f"""Grade the following student answer on a scale of 0 to {points} points.

            QUESTION:
            {question}

            EXPECTED ANSWER / RUBRIC:
            {expected}

            STUDENT ANSWER:
            {student}

            Provide your response in this exact format:
            SCORE: [number between 0 and {points}]
            FEEDBACK: [constructive feedback explaining the grade]

            Be fair and thorough. Award partial credit for partially correct answers."""
    
    def _parse_llm_response(self, response: str, max_points: float) -> Tuple[float, str]:
        """Parse Gemini response to extract score and feedback."""
        lines = response.strip().split('\n')
        score = 0.0
        feedback = response
        
        for line in lines:
            if line.startswith("SCORE:"):
                try:
                    score_text = line.replace("SCORE:", "").strip()
                    score = float(score_text)
                    score = max(0.0, min(score, max_points))
                except ValueError:
                    pass
            elif line.startswith("FEEDBACK:"):
                feedback = line.replace("FEEDBACK:", "").strip()
                idx = lines.index(line)
                if idx + 1 < len(lines):
                    feedback = '\n'.join(lines[idx:]).replace("FEEDBACK:", "").strip()
                break
        
        return round(score, 4), feedback

class GraderFactory:
    """Factory for creating grader instances."""
    
    @staticmethod
    def create_grader(strategy: str = "mock", **kwargs) -> BaseGrader:
        """
        Create a grader instance based on strategy.
        
        Args:
            strategy: "mock", "openai", "claude", or "gemini"
            **kwargs: Additional arguments (api_key, model, etc.)
        
        Returns:
            BaseGrader instance
        """
        strategy = strategy.lower()
        
        if strategy == "mock":
            return MockGrader()
        elif strategy == "gemini":
            return GeminiGrader(**kwargs)
        else:
            raise ValueError(f"Unknown grading strategy: {strategy}")



def grade_question(question, answer_obj, grader: Optional[BaseGrader] = None) -> Dict[str, Any]:
    """
    Grade a Question instance against an Answer object.
    
    Args:
        question: Question model instance
        answer_obj: Answer object with answer_text or selected_choice
        grader: Grader instance (defaults to MockGrader)
    
    Returns:
        Dict with points_awarded, points_possible, and feedback
    """
    if grader is None:
        grader = MockGrader()
    
    qtype = question.question_type
    question_text = getattr(question, "question_text", "")
    
    if qtype == "mcq":
        expected = question.expected_answer
        selected = getattr(answer_obj, "selected_choice", None) or getattr(answer_obj, "answer_text", None)
        
        # Normalize expected answer
        if isinstance(expected, dict) and "key" in expected:
            expected_key = expected.get("key")
        else:
            expected_key = expected
        
        awarded, possible, feedback = grader.grade_mcq(expected_key, selected, question.points)
    else:
        # Text question
        expected = question.expected_answer
        student_answer = getattr(answer_obj, "answer_text", "")
        awarded, possible, feedback = grader.grade_text(question_text, expected, student_answer, question.points)
    
    return {
        "points_awarded": awarded,
        "points_possible": possible,
        "feedback": feedback
    }

def get_default_grader() -> BaseGrader:
    """Get the default grader from environment settings."""
    strategy = os.getenv("GRADING_STRATEGY", "mock").lower()
    
    try:
        return GraderFactory.create_grader(strategy)
    except Exception as e:
        print(f"Failed to create {strategy} grader: {e}. Falling back to mock.")
        return MockGrader()