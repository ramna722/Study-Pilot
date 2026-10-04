import json

from models import QuizInput, QuizOutput, QuizQuestion
from prompt import build_quiz_prompt
from groq_client import GroqClient


class QuizAgent:

    def __init__(self):

        # Create Groq client
        self.llm = GroqClient()

    def generate_quiz(self, quiz_input: QuizInput) -> QuizOutput:

        # Build prompt
        prompt = build_quiz_prompt(
            quiz_input.topic,
            quiz_input.context,
            quiz_input.num_questions,
            quiz_input.difficulty,
            quiz_input.question_type
        )

        print("\nGenerated Prompt:")
        print(prompt)

        # Send prompt to Groq
        response = self.llm.generate(prompt)

        print("\nGroq Response:")
        print(response)

        # Remove Markdown code fences if Groq adds them
        response = response.strip()

        if response.startswith("```json"):
            response = response[7:]

        elif response.startswith("```"):
            response = response[3:]

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        # Convert JSON response into Python dictionary
        data = json.loads(response)

        # Get questions from Groq response
        questions_data = data.get("questions")

        # If Groq uses "quiz" instead of "questions"
        if questions_data is None:
            questions_data = data.get("quiz")

        if questions_data is None:
            raise ValueError(
                "Groq response does not contain 'questions' or 'quiz'."
            )

        # Create QuizQuestion objects
        questions = []

        for item in questions_data:

            # Support both correct_answer and answer
            correct_answer = item.get("correct_answer")

            if correct_answer is None:
                correct_answer = item.get("answer")

            question = QuizQuestion(
                question=item["question"],
                options=item["options"],
                correct_answer=correct_answer,
                explanation=item["explanation"]
            )

            questions.append(question)

        # Return final QuizOutput
        return QuizOutput(
            topic=quiz_input.topic,
            questions=questions
        )