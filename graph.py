"""
graph.py  --  the MANAGER (orchestrator) of StudyPilot, built with LangGraph.

It decides which agent runs first, which runs next, and passes the shared
"state" (the notebook) from agent to agent.

Order:
  Phase 1 (student uploads notes):
      document -> topic -> planner -> quiz -> END   (student now answers the quiz)
  Phase 2 (student sends answers):
      evaluator -> recommendation -> (weak topics?) -> quiz -> END
                                   -> (no weak topics) -> END

Each teammate's file must contain a function with EXACTLY this name:
  agents/document_agent.py       -> document_agent_node(state)
  agents/topic_agent.py          -> topic_agent_node(state)
  agents/planner_agent.py        -> planner_agent_node(state)
  agents/quiz_agent.py           -> quiz_agent_node(state)
  agents/evaluator_agent.py      -> evaluator_agent_node(state)
  agents/recommendation_agent.py -> recommendation_agent_node(state)

If a teammate's agent is not on GitHub yet, a FAKE stand-in is used, so the
whole flow can still be tested today. Real agents replace the fakes
automatically when their files appear.
"""
import importlib
import inspect
from datetime import date, timedelta
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


# ---------- 1. The shared notebook (all names must be listed here) ----------
class StudyState(TypedDict, total=False):
    chunks: list
    topics: list
    study_plan: list
    questions: list
    student_answers: list
    evaluation: list
    weak_topics: list
    recommendation: str
    document: str           # path of the uploaded file (Document Agent reads this)
    file: str               # (Document Agent also accepts this name)
    exam_date: str          # input from the student (Planner Agent needs it)
    daily_hours: float      # input from the student (Planner Agent needs it)


# ---------- 2. Fake stand-ins (used only if the real agent is missing) ----------
def _fake_document(state):
    with open("sample_data/sample_notes.txt", encoding="utf-8") as f:
        text = f.read()
    return {"chunks": [p for p in text.split("\n\n") if p.strip()]}


def _fake_planner(state):
    plan = [{"day": i + 1, "topic_id": t["id"], "topic": t["topic"]}
            for i, t in enumerate(state["topics"])]
    return {"study_plan": plan}


def _fake_quiz(state):
    qs = [{"topic_id": t["id"], "question": "What is " + t["topic"] + "?"}
          for t in state["topics"][:3]]
    return {"questions": qs}


def _fake_evaluator(state):
    return {"evaluation": [{"topic_id": "t1", "correct": False}],
            "weak_topics": ["t1"]}


def _fake_recommendation(state):
    return {"recommendation": "Revise topic(s): " + ", ".join(state.get("weak_topics", []))}


FAKES = {
    "document": _fake_document,
    "planner": _fake_planner,
    "quiz": _fake_quiz,
    "evaluator": _fake_evaluator,
    "recommendation": _fake_recommendation,
}


def load_agent(name):
    """Use the real agent if it exists, otherwise the fake one.

    Teammates named their functions differently, so we accept either
    <name>_agent_node(state)  or  <name>_agent(state).
    """
    try:
        module = importlib.import_module("agents." + name + "_agent")
    except Exception as error:  # file missing OR the file has an error inside
        print("[FAKE]  " + name + " agent -> could not import: " + repr(error))
        return FAKES[name]

    for func_name in (name + "_agent_node", name + "_agent"):
        func = getattr(module, func_name, None)
        if inspect.isfunction(func):  # must be a function (not a class)
            print("[real]  " + name + " agent  (function: " + func_name + ")")
            return func

    print("[FAKE]  " + name + " agent -> no function named "
          + name + "_agent_node or " + name + "_agent")
    return FAKES[name]


# ---------- 3. Decisions ----------
def route_start(state):
    """New upload -> start from the beginning. Answers present -> go grade them."""
    return "evaluator" if state.get("student_answers") else "document"


def after_recommendation(state):
    """Weak topics found -> make more questions. Otherwise finish."""
    return "quiz" if state.get("weak_topics") else "end"


# ---------- 4. Build the graph ----------
def build_graph():
    graph = StateGraph(StudyState)

    graph.add_node("document", load_agent("document"))
    graph.add_node("topic", load_agent("topic"))
    graph.add_node("planner", load_agent("planner"))
    graph.add_node("quiz", load_agent("quiz"))
    graph.add_node("evaluator", load_agent("evaluator"))
    graph.add_node("recommendation", load_agent("recommendation"))

    graph.add_conditional_edges(START, route_start,
                                {"document": "document", "evaluator": "evaluator"})
    graph.add_edge("document", "topic")
    graph.add_edge("topic", "planner")
    graph.add_edge("planner", "quiz")
    graph.add_edge("quiz", END)                       # wait for the student's answers
    graph.add_edge("evaluator", "recommendation")
    graph.add_conditional_edges("recommendation", after_recommendation,
                                {"quiz": "quiz", "end": END})
    return graph.compile()


# ---------- 5. Try it:  python graph.py ----------
if __name__ == "__main__":
    app = build_graph()

    print("\n--- Phase 1: student uploads notes ---")
    exam_date = (date.today() + timedelta(days=14)).isoformat()   # example: 14 days from today
    state = app.invoke({
        "document": "sample_data/sample_notes.txt",
        "exam_date": exam_date,
        "daily_hours": 2,
    })
    print("topics   :", [t["topic"] for t in state["topics"]])
    print("plan     :", str(state["study_plan"])[:400], "...")
    print("questions:", len(state["questions"]), "questions, e.g.", state["questions"][0]["question"])

    print("\n--- Phase 2: student sends answers ---")
    try:
        # NOTE: this answer format is a guess. The Evaluator Agent decides the real format.
        state["student_answers"] = [{"topic_id": "t1", "answer": "my answer"}]
        state = app.invoke(state)
        print("weak     :", state["weak_topics"])
        print("advice   :", state["recommendation"])
    except Exception as error:
        print("Phase 2 stopped:", repr(error))
        print("(Phase 1 worked. Phase 2 needs the answer format the Evaluator Agent expects.)")
