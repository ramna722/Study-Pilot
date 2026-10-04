import os
from groq import Groq


class GroqClient:

    def __init__(self):

        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Please set the API key in PowerShell."
            )

        self.client = Groq(api_key=api_key)

    def generate(self, prompt):

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful Quiz Agent for StudyPilot."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        return response.choices[0].message.content