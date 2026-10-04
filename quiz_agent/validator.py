from models import QuizOutput


class QuizValidator:

    def validate(self, quiz: QuizOutput) -> bool:

        # Check that quiz contains questions
        if not quiz.questions:
            print("Validation Error: No questions found.")
            return False

        # Check every question
        for number, question in enumerate(quiz.questions, start=1):

            # Check question text
            if not question.question.strip():
                print(f"Validation Error: Question {number} is empty.")
                return False

            # Check exactly 4 options
            if len(question.options) != 4:
                print(
                    f"Validation Error: Question {number} "
                    f"must have exactly 4 options."
                )
                return False

            # Check that options are not empty
            for option in question.options:
                if not option.strip():
                    print(
                        f"Validation Error: Question {number} "
                        f"contains an empty option."
                    )
                    return False

            # Check correct answer exists
            if not question.correct_answer.strip():
                print(
                    f"Validation Error: Question {number} "
                    f"has no correct answer."
                )
                return False

            # Check correct answer is one of the options
            if question.correct_answer not in question.options:
                print(
                    f"Validation Error: Correct answer for "
                    f"Question {number} is not in the options."
                )
                return False

            # Check explanation
            if not question.explanation.strip():
                print(
                    f"Validation Error: Question {number} "
                    f"has no explanation."
                )
                return False

        print("Quiz validation successful!")
        return True