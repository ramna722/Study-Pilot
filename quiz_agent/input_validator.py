from models import QuizInput


class QuizInputValidator:

    def validate(self, quiz_input: QuizInput) -> bool:

        # Check topic
        if not quiz_input.topic.strip():
            print("Input Validation Error: Topic is required.")
            return False

        # Check study material
        if not quiz_input.context.strip():
            print("Input Validation Error: Study material is required.")
            return False

        # Check number of questions
        if quiz_input.num_questions <= 0:
            print("Input Validation Error: Number of questions must be greater than 0.")
            return False

        # Check maximum number of questions
        if quiz_input.num_questions > 20:
            print("Input Validation Error: Maximum 20 questions are allowed.")
            return False

        # Check difficulty
        valid_difficulties = ["easy", "medium", "hard"]

        if quiz_input.difficulty.lower() not in valid_difficulties:
            print("Input Validation Error: Difficulty must be easy, medium, or hard.")
            return False

        # Check question type
        valid_question_types = [
            "mcq",
            "true_false",
            "short_answer"
        ]

        if quiz_input.question_type.lower() not in valid_question_types:
            print("Input Validation Error: Question type must be mcq, true_false, or short_answer.")
            return False

        print("Input validation successful!")
        return True