"""
app_live.py  --  StudyPilot app connected to the REAL agents.

Run:  streamlit run app_live.py

Flow:  Upload -> Topic Agent -> Planner Agent -> Quiz Agent
       -> student answers -> Evaluator Agent -> Recommendation Agent
       -> (weak topics?) -> new quiz for the weak topics
"""
from datetime import date, timedelta

import streamlit as st

from agents.document_agent import extract_chunks
from agents.topic_agent import topic_agent_node
from agents.planner_agent import planner_agent_node
from agents.quiz_agent import quiz_agent_node
from agents.evaluator_agent import evaluator_agent_node
from agents.recommendation_agent import recommendation_agent

st.set_page_config(page_title="StudyPilot", page_icon="🎓", layout="wide")


# ---------- small helpers ----------
def run_agent(agent, state):
    """Run one agent. It reads the shared state and writes its result into it."""
    out = agent(state)
    if isinstance(out, dict) and out is not state:
        state.update(out)
    return state


def option_text(option):
    if isinstance(option, dict):
        return str(option.get("option_text") or option.get("text") or option)
    return str(option)


def topic_name(state, topic_id):
    for t in state.get("topics", []):
        if t.get("id") == topic_id:
            return t.get("topic", str(topic_id))
    return str(topic_id)


if "state" not in st.session_state:
    st.session_state["state"] = {}   # the shared notebook of all agents
if "round" not in st.session_state:
    st.session_state["round"] = 0    # changes when a new quiz is created

# ---------- page ----------
st.title("🎓 StudyPilot")
st.caption("Study → Practice → Evaluate → Find weak topics → Improve")

with st.sidebar:
    st.header("Your exam")
    exam_date = st.date_input("Exam date", value=date.today() + timedelta(days=14),
                              min_value=date.today())
    daily_hours = st.number_input("Study hours per day", min_value=0.5, max_value=12.0,
                                  value=2.0, step=0.5)
    st.caption("Document → Topic → Planner → Quiz → Evaluator → Recommendation")

tab_upload, tab_plan, tab_quiz, tab_results = st.tabs(
    ["1. Upload", "2. Topics & plan", "3. Quiz", "4. Results"])

# ---------- Tab 1: upload + run the first agents ----------
with tab_upload:
    st.subheader("Upload your study material")
    files = st.file_uploader("PDF, TXT or Markdown", type=["pdf", "txt", "md"],
                             accept_multiple_files=True)
    if st.button("Analyse my material", type="primary", disabled=not files):
        try:
            chunks = []
            for f in files:
                chunks.extend(extract_chunks(f))                      # Document Agent
            new_state = {"chunks": chunks,
                         "exam_date": exam_date.isoformat(),
                         "daily_hours": float(daily_hours)}
            with st.spinner("Topic Agent is reading your notes..."):
                run_agent(topic_agent_node, new_state)                # Topic Agent
            with st.spinner("Planner Agent is building your study plan..."):
                run_agent(planner_agent_node, new_state)              # Planner Agent
            with st.spinner("Quiz Agent is writing questions (about a minute)..."):
                run_agent(quiz_agent_node, new_state)                 # Quiz Agent
            st.session_state["state"] = new_state
            st.session_state["round"] += 1
            st.success("Done! Open the other tabs.")
        except Exception as error:
            st.error("Something went wrong: " + str(error))

# ---------- Tab 2: topics and plan ----------
with tab_plan:
    state = st.session_state["state"]
    if "topics" not in state:
        st.info("Upload and analyse your material first.")
    else:
        st.subheader("Important topics")
        for t in state["topics"]:
            with st.expander(t["topic"] + "  ·  " + t["importance"]):
                st.write(t.get("summary", ""))
                st.caption("Key concepts: " + ", ".join(t.get("key_concepts", [])))
        st.subheader("Your study plan")
        plan = state.get("study_plan", {})
        days = plan.get("days", []) if isinstance(plan, dict) else []
        for d in days:
            names = ", ".join(str(x.get("topic")) + " (" + str(x.get("hours")) + "h)"
                              for x in d.get("topics", []))
            st.write("**Day " + str(d.get("day")) + " · " + str(d.get("date")) + "**: " + names)
        if not days:
            st.json(plan)

# ---------- Tab 3: quiz ----------
with tab_quiz:
    state = st.session_state["state"]
    questions = state.get("questions", [])
    if not questions:
        st.info("Upload and analyse your material first.")
    else:
        rnd = st.session_state["round"]
        answers = []
        for q in questions:
            st.markdown("**Q" + str(q["question_id"]) + ". " + str(q["question"])
                        + "**  \n*Topic: " + str(q.get("topic")) + "*")
            options = [option_text(o) for o in q.get("options", [])]
            choice = st.radio("Your answer", options, index=None,
                              key="r" + str(rnd) + "_q" + str(q["question_id"]),
                              label_visibility="collapsed")
            answers.append({"question_id": q["question_id"], "student_answer": choice})
        if st.button("Submit answers", type="primary"):
            if any(a["student_answer"] is None for a in answers):
                st.warning("Please answer every question first.")
            else:
                try:
                    state["student_answers"] = answers
                    with st.spinner("Evaluator Agent is checking your answers..."):
                        run_agent(evaluator_agent_node, state)        # Evaluator Agent
                        run_agent(recommendation_agent, state)        # Recommendation Agent
                    st.success("Done! Open the Results tab.")
                except Exception as error:
                    st.error("Something went wrong: " + str(error))

# ---------- Tab 4: results ----------
with tab_results:
    state = st.session_state["state"]
    evaluation = state.get("evaluation") or []
    if not evaluation:
        st.info("Take the quiz and press 'Submit answers' to see your results.")
    else:
        right = sum(1 for e in evaluation if e.get("evaluation") == "correct")
        st.metric("Your score", str(right) + " / " + str(len(evaluation)))
        for e in evaluation:
            kind = e.get("evaluation")
            icon = "✅" if kind == "correct" else "🟡" if kind == "partially_correct" else "❌"
            st.write(icon + " Q" + str(e.get("question_id")) + " ("
                     + topic_name(state, e.get("topic_id")) + "): " + str(e.get("explanation", "")))

        weak = state.get("weak_topics") or []
        if weak:
            st.warning("Weak topics: " + ", ".join(topic_name(state, w) for w in weak))
        else:
            st.success("No weak topics. Great job!")

        st.subheader("What to study next")
        rec = state.get("recommendation")
        recs = rec.get("recommendations") if isinstance(rec, dict) else None
        if recs:
            for item in recs:
                st.write("• " + str(item))
        elif rec:
            st.write(rec)
        if rec:
            with st.expander("Raw recommendation data"):
                st.json(rec)

        if weak and st.button("Practice my weak topics", type="primary"):
            try:
                with st.spinner("Quiz Agent is writing new questions for your weak topics..."):
                    run_agent(quiz_agent_node, state)   # picks the weak topics by itself
                state["evaluation"] = []
                st.session_state["round"] += 1
                st.success("New questions are ready in the Quiz tab.")
            except Exception as error:
                st.error("Something went wrong: " + str(error))
