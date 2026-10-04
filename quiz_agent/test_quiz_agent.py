from models import QuizInput
from quiz_agent import QuizAgent
from validator import QuizValidator
from input_validator import QuizInputValidator


def main():

    quiz_input = QuizInput(
        topic="Database Indexing",
        context="""
        An index is a data structure used by a database
        to improve the speed of data retrieval operations.
        Indexes can help the database find records more efficiently.
        """,
        num_questions=3,
        difficulty="medium",
        question_type="mcq"
    )

    # Step 1: Validate input
    input_validator = QuizInputValidator()

    if not input_validator.validate(quiz_input):
        print("\nInvalid quiz input.")
        return

    # Step 2: Create Quiz Agent
    agent = QuizAgent()

    # Step 3: Generate quiz
    quiz = agent.generate_quiz(quiz_input)

    # Step 4: Validate generated quiz
    quiz_validator = QuizValidator()

    if not quiz_validator.validate(quiz):
        print("\nQuiz generation failed validation.")
        return

    # Step 5: Display quiz
    print("\n========== QUIZ ==========")
    print("Topic:", quiz.topic)

    for number, question in enumerate(quiz.questions, start=1):

        print(f"\nQ{number}. {question.question}")

        for option in question.options:
            print("-", option)

        print("Answer:", question.correct_answer)
        print("Explanation:", question.explanation)


if __name__ == "__main__":
    main()