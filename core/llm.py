"""
core/llm.py
One shared function that every agent uses to talk to the AI model.
Switch between Groq and Gemini by changing LLM_PROVIDER in your .env file.
"""
import os

try:  # python-dotenv reads your .env file. Optional (not needed in Colab).
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEFAULT_SYSTEM = "You are a helpful study assistant."


def ask_llm(prompt: str, system: str = DEFAULT_SYSTEM) -> str:
    """Send a prompt to the chosen AI model and return its text answer."""
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    if provider == "groq":
        return _ask_groq(prompt, system)
    if provider == "gemini":
        return _ask_gemini(prompt, system)
    raise ValueError("LLM_PROVIDER must be 'groq' or 'gemini', got: " + provider)


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


def _ask_gemini(prompt: str, system: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=prompt,
        config=types.GenerateContentConfig(system_instruction=system, temperature=0.2),
    )
    return response.text
