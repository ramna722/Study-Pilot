"""
agents/quiz_agent.py  --  GRAPH ADAPTER for the Quiz Agent

The real Quiz Agent code lives in the folder  quiz_agent/  (written by a teammate).
This small file connects it to the shared "state" so graph.py can use it.
Nothing inside the quiz_agent/ folder needs to change.

Reads : state["topics"]  (from Topic Agent), state["chunks"] (from Document Agent),
        state["weak_topics"] (optional, topic ids -> only quiz those topics)
Writes: state["questions"]  = list of dicts like
    {"topic_id": "t1", "topic": "Registers", "question": "...",
     "options": ["A", "B", "C", "D"], "correct_answer": "...", "explanation": "..."}
"""
import os
import sys

try:  # read the .env file (API keys)
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# The teammate's code uses imports like "from models import ...", which only work
# when its own folder is on Python's search path. So we add that folder.
_QUIZ_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "quiz_agent")
if _QUIZ_DIR not in sys.path:
    sys.path.insert(0, _QUIZ_DIR)

from models import QuizInput        # noqa: E402  (these come from quiz_agent/ folder)
from quiz_agent import QuizAgent    # noqa: E402  (quiz_agent/quiz_agent.py)

MAX_TOPICS = 5            # quiz at most this many topics (keeps API calls low)
QUESTIONS_PER_TOPIC = 2
MAX_CONTEXT_CHARS = 3000  # how much study text we give the Quiz Agent per topic


class _GeminiLLM:
    """Used only when GROQ_API_KEY is missing: lets the Quiz Agent use our shared Gemini."""

    def generate(self, prompt):
        from core.llm import ask_llm
        return ask_llm(prompt, "You are a helpful Quiz Agent for StudyPilot.")


def _make_agent():
    if os.getenv("GROQ_API_KEY"):
        return QuizAgent()                      # teammate's original setup (Groq)
    agent = QuizAgent.__new__(QuizAgent)        # no Groq key -> use Gemini instead
    agent.llm = _GeminiLLM()
    return agent


def _pick_topics(state):
    topics = state["topics"]
    weak_ids = state.get("weak_topics") or []
    if weak_ids:
        chosen = [t for t in topics if t["id"] in weak_ids]
        if chosen:
            return chosen
    return topics[:MAX_TOPICS]


def _build_context(topic, chunks):
    """Study text for one topic: its summary + key concepts + notes that mention it."""
    concepts = topic.get("key_concepts", [])
    parts = [topic.get("summary", ""), "Key concepts: " + ", ".join(concepts)]
    words = [topic["topic"].lower()] + [c.lower() for c in concepts]
    for chunk in chunks:
        text = chunk["text"] if isinstance(chunk, dict) else str(chunk)
        if any(w in text.lower() for w in words):
            parts.append(text)
        if sum(len(p) for p in parts) > MAX_CONTEXT_CHARS:
            break
    return "\n\n".join(parts)[:MAX_CONTEXT_CHARS]


def _get(obj, name):
    return obj[name] if isinstance(obj, dict) else getattr(obj, name)


def quiz_agent_node(state):
    """Used by graph.py: reads state["topics"], writes state["questions"]."""
    if not state.get("topics"):
        raise ValueError("state has no 'topics'. The Topic Agent must run first.")

    agent = _make_agent()
    chunks = state.get("chunks", [])
    all_questions = []

    for topic in _pick_topics(state):
        try:
            result = agent.generate_quiz(QuizInput(
                topic=topic["topic"],
                context=_build_context(topic, chunks),
                num_questions=QUESTIONS_PER_TOPIC,
                difficulty="medium",
                question_type="multiple_choice",
            ))
        except Exception as error:  # one bad topic should not stop the others
            print("Quiz Agent skipped topic '" + topic["topic"] + "': " + str(error))
            continue
        for q in result.questions:
            all_questions.append({
                "topic_id": topic["id"],
                "topic": topic["topic"],
                "question": _get(q, "question"),
                "options": _get(q, "options"),
                "correct_answer": _get(q, "correct_answer"),
                "explanation": _get(q, "explanation"),
            })

    if not all_questions:
        raise ValueError("Quiz Agent could not create any questions.")
    state["questions"] = all_questions
    return state


if __name__ == "__main__":  # quick test:  python -m agents.quiz_agent
    demo = {
        "topics": [{"id": "t1", "topic": "Registers", "importance": "High",
                    "summary": "Small fast storage inside the CPU.",
                    "key_concepts": ["EAX", "EBX"]}],
        "chunks": ["Registers are small storage inside the CPU. EAX and EBX are general-purpose registers."],
    }
    for q in quiz_agent_node(demo)["questions"]:
        print(q)
