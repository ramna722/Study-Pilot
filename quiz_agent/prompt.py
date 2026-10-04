def build_quiz_prompt(
    topic,
    context,
    num_questions,
    difficulty,
    question_type
):
    prompt = f"""
You are the Quiz Agent of StudyPilot.

Your task is to generate a quiz using the student's study material.

Topic:
{topic}

Study Material:
{context}

Requirements:
- Generate {num_questions} questions.
- Difficulty: {difficulty}
- Question type: {question_type}
- Questions must be based on the provided study material.
- Each question must have four options.
- Provide one correct answer.
- Provide a short explanation for the correct answer.
- Do not add information that is unrelated to the provided material.

Return the quiz in structured JSON format.
"""

    return prompt