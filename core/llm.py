"""
core/llm.py
One shared function that every agent uses to talk to the AI model.
Switch between Groq and Gemini by changing LLM_PROVIDER in your .env file.

If the AI says "503 busy" (or 429 rate limit), this file waits and tries again
by itself, and on later tries it switches to a backup Gemini model.
"""
import os
import time

try:  # python-dotenv reads your .env file. Optional (not needed in Colab).
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEFAULT_SYSTEM = "You are a helpful study assistant."
MAX_TRIES = 5
BUSY_WORDS = ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "overloaded")


def ask_llm(prompt: str, system: str = DEFAULT_SYSTEM) -> str:
    """Send a prompt to the chosen AI model and return its text answer."""
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    if provider not in ("groq", "gemini"):
        raise ValueError("LLM_PROVIDER must be 'groq' or 'gemini', got: " + provider)

    for attempt in range(MAX_TRIES):
        try:
            if provider == "groq":
                return _ask_groq(prompt, system)
            return _ask_gemini(prompt, system, use_backup=attempt >= 2)
        except Exception as error:
            busy = any(word in str(error) for word in BUSY_WORDS)
            if busy and attempt < MAX_TRIES - 1:
                wait = 4 * (attempt + 1)  # 4s, 8s, 12s, 16s
                print("AI is busy, trying again in " + str(wait) + " seconds...")
                time.sleep(wait)
                continue
            raise


def _ask_groq(prompt: str, system: str) -> str:
    from groq import Groq  # imported here so you only need the package you use

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,  # low = more consistent, less random
    )
    return response.choices[0].message.content


def _ask_gemini(prompt: str, system: str, use_backup: bool = False) -> str:
    from google import genai
    from google.genai import types

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if use_backup:  # the main model is busy: try the backup model
        model = os.getenv("GEMINI_BACKUP_MODEL", "gemini-2.5-flash")

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=system, temperature=0.2),
    )
    return response.text
