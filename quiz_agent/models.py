from dataclasses import dataclass
from typing import List


@dataclass
class QuizInput:
    topic: str
    context: str
    num_questions: int
    difficulty: str = "medium"
    question_type: str = "mcq"


@dataclass
class QuizQuestion:
    question: str
    options: List[str]
    correct_answer: str
    explanation: str


@dataclass
class QuizOutput:
    topic: str
    questions: List[QuizQuestion]