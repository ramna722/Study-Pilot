"""StudyPilot dashboard demo.

Run with: streamlit run app.py
"""
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

from agents.document_agent import extract_chunks


st.set_page_config(page_title="StudyPilot", page_icon="SP", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@700;800&display=swap');
    :root {
      --ink: #17252a;
      --muted: #6e7f82;
      --line: #e4eceb;
      --surface: #ffffff;
      --canvas: #f7faf9;
      --accent: #167c80;
      --accent-soft: #e2f2f0;
      --good: #2d9a72;
      --warn: #d99b3d;
      --risk: #d86a68;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: var(--ink); }
    .stApp { background: var(--canvas); }
    [data-testid="stSidebar"] { background: #eef5f3; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] > div:first-child { padding: 30px 20px; }
    h1, h2, h3 { font-family: 'Manrope', sans-serif; letter-spacing: 0; color: var(--ink); }
    h1 { font-size: 2rem !important; margin-bottom: 0.3rem !important; }
    h2 { font-size: 1.35rem !important; }
    .block-container { max-width: 1180px; padding: 2.5rem 3rem 4rem; }
    .brand { display: flex; align-items: center; gap: 11px; margin-bottom: 34px; }
    .brand-mark { width: 38px; height: 38px; display: grid; place-items: center; border-radius: 11px; background: var(--accent); color: white; font-family: 'Manrope'; font-weight: 800; font-size: 14px; }
    .brand-name { font-family: 'Manrope'; font-size: 18px; font-weight: 800; }
    .brand-sub { color: var(--muted); font-size: 11px; margin-top: 2px; }
    .eyebrow { color: var(--accent); text-transform: uppercase; font-size: 11px; font-weight: 700; letter-spacing: .08em; margin-bottom: 7px; }
    .muted { color: var(--muted); }
    .card { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 21px; box-shadow: 0 5px 18px rgba(23, 57, 58, .035); }
    .metric-label { color: var(--muted); font-size: 13px; margin-bottom: 8px; }
    .metric-value { font-family: 'Manrope'; font-size: 31px; font-weight: 800; line-height: 1; }
    .metric-foot { color: var(--good); font-size: 12px; margin-top: 10px; }
    .section-head { display: flex; justify-content: space-between; align-items: baseline; margin: 30px 0 13px; }
    .section-title { font-family: 'Manrope'; font-weight: 800; font-size: 17px; }
    .section-note { color: var(--muted); font-size: 12px; }
    .plan-row { display: flex; gap: 13px; align-items: center; padding: 14px 0; border-bottom: 1px solid #edf2f1; }
    .plan-row:last-child { border-bottom: 0; padding-bottom: 0; }
    .plan-time { width: 52px; color: var(--muted); font-size: 12px; }
    .plan-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); }
    .plan-name { font-weight: 600; font-size: 14px; flex: 1; }
    .plan-duration { color: var(--muted); font-size: 12px; }
    .topic-row { margin: 14px 0 20px; }
    .topic-line { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 7px; }
    .bar { height: 7px; border-radius: 8px; background: #edf2f1; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 8px; }
    .bar-risk { background: var(--risk); }
    .bar-warn { background: var(--warn); }
    .bar-good { background: var(--good); }
    .next-card { background: #dff1ed; border: 1px solid #c7e6df; border-radius: 12px; padding: 25px 28px; display: flex; align-items: center; justify-content: space-between; gap: 24px; }
    .next-title { font-family: 'Manrope'; font-size: 22px; font-weight: 800; margin: 5px 0 7px; }
    .next-copy { color: #52706f; font-size: 13px; max-width: 600px; }
    .agent-strip { border: 1px solid var(--line); border-radius: 10px; background: white; padding: 14px 18px; margin-bottom: 22px; }
    .agent-step { display: inline-flex; align-items: center; gap: 7px; color: var(--muted); font-size: 11px; margin-right: 23px; }
    .agent-step.active { color: var(--accent); font-weight: 700; }
    .step-dot { width: 8px; height: 8px; border-radius: 50%; background: #cbd8d7; }
    .active .step-dot { background: var(--accent); box-shadow: 0 0 0 4px var(--accent-soft); }
    .upload-zone { padding: 50px 25px; text-align: center; border: 1.5px dashed #a8c7c2; border-radius: 12px; background: #fbfefd; }
    .upload-icon { color: var(--accent); font-size: 28px; margin-bottom: 7px; }
    .file-row { display: flex; align-items: center; gap: 15px; border-bottom: 1px solid var(--line); padding: 17px 2px; }
    .file-icon { width: 36px; height: 36px; border-radius: 8px; display: grid; place-items: center; background: var(--accent-soft); color: var(--accent); font-size: 11px; font-weight: 700; }
    .file-name { font-weight: 600; font-size: 14px; flex: 1; }
    .file-type, .file-pages { color: var(--muted); font-size: 12px; }
    .file-pages { width: 70px; text-align: right; }
    .topic-card { min-height: 155px; }
    .topic-card-title { font-family: 'Manrope'; font-size: 16px; font-weight: 800; margin: 4px 0 9px; }
    .tag { display: inline-block; background: #f1f6f5; color: var(--muted); border-radius: 4px; padding: 4px 7px; font-size: 11px; margin: 3px 3px 0 0; }
    .quiz-number { color: var(--accent); font-size: 12px; font-weight: 700; margin-bottom: 13px; }
    .quiz-question { font-family: 'Manrope'; font-size: 25px; font-weight: 800; line-height: 1.25; max-width: 760px; margin-bottom: 25px; }
    .score { font-family: 'Manrope'; font-size: 54px; font-weight: 800; color: var(--accent); }
    .score-label { color: var(--muted); font-size: 13px; }
    .nav-label { color: var(--muted); text-transform: uppercase; letter-spacing: .08em; font-size: 10px; font-weight: 700; margin: 12px 0 8px 5px; }
    div.stButton > button { border-radius: 7px; border: 1px solid var(--line); font-weight: 600; color: var(--ink); background: white; }
    div.stButton > button[kind="primary"] { color: white; background: var(--accent); border-color: var(--accent); }
    div.stButton > button:hover { border-color: var(--accent); color: var(--accent); }
    </style>
    """,
    unsafe_allow_html=True,
)


TOPICS = [
    {"name": "Addressing Modes", "score": 38, "color": "risk", "detail": "Needs review", "concepts": ["Immediate", "Direct", "Indirect"]},
    {"name": "Memory Architecture", "score": 56, "color": "warn", "detail": "Making progress", "concepts": ["RAM", "ROM", "Addresses"]},
    {"name": "Registers", "score": 84, "color": "good", "detail": "Strong", "concepts": ["EAX", "EBX", "Stack pointer"]},
]


def init_state():
    defaults = {
        "page": "Dashboard",
        "files": [],
        "chunks": [],
        "quiz_index": 0,
        "quiz_submitted": False,
        "quiz_answer": None,
        "important_topics": {topic["name"]: True for topic in TOPICS},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def navigate(page):
    st.session_state.page = page
    st.session_state.quiz_submitted = False
    st.rerun()


def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="brand"><div class="brand-mark">SP</div><div><div class="brand-name">StudyPilot</div><div class="brand-sub">Your study command centre</div></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="nav-label">Workspace</div>', unsafe_allow_html=True)
        for page in ["Dashboard", "Materials", "Study plan", "Quizzes", "Progress"]:
            if st.button(page, key=f"nav_{page}", use_container_width=True, type="primary" if st.session_state.page == page else "secondary"):
                navigate(page)
        st.markdown('<div class="nav-label" style="margin-top:35px">Agent pipeline</div>', unsafe_allow_html=True)
        for label, state in [("Document", "Ready"), ("Topics", "Ready"), ("Planner", "Today"), ("Evaluator", "Next")]:
            color = "#2d9a72" if state == "Ready" else "#167c80"
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:9px 4px;color:#6e7f82;font-size:12px"><span>{label} Agent</span><span style="color:{color};font-weight:700">{state}</span></div>', unsafe_allow_html=True)
        st.markdown('<div style="position:fixed;bottom:25px;color:#8a9a9a;font-size:11px">Exam: Computer Architecture · 18 days</div>', unsafe_allow_html=True)


def agent_strip(active):
    steps = ["Document", "Topics", "Planner", "Quiz", "Evaluate", "Recommend"]
    html = '<div class="agent-strip">'
    for index, step in enumerate(steps):
        class_name = "active" if step == active else ""
        html += f'<span class="agent-step {class_name}"><span class="step-dot"></span>{step}</span>'
    st.markdown(html + "</div>", unsafe_allow_html=True)


def header(eyebrow, title, subtitle):
    st.markdown(f'<div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p class="muted">{subtitle}</p>', unsafe_allow_html=True)


def metric(label, value, foot):
    st.markdown(f'<div class="card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-foot">{foot}</div></div>', unsafe_allow_html=True)


def dashboard():
    header("Monday, 4 October", "Good morning, Rabia", "You have a clear path today. Let’s make the next study session count.")
    agent_strip("Recommend")
    metric_cols = st.columns(3)
    with metric_cols[0]: metric("Exam readiness", "68%", "+8% this week")
    with metric_cols[1]: metric("Topics found", "12", "3 need attention")
    with metric_cols[2]: metric("Quizzes taken", "8", "+2 this week")

    st.markdown('<div class="section-head"><span class="section-title">Today\'s plan</span><span class="section-note">3 of 4 sessions planned</span></div>', unsafe_allow_html=True)
    left, right = st.columns([1.15, .85], gap="large")
    with left:
        st.markdown('<div class="card"><div class="plan-row"><div class="plan-time">09:00</div><div class="plan-dot"></div><div class="plan-name">Review Addressing Modes</div><div class="plan-duration">45 min</div></div><div class="plan-row"><div class="plan-time">11:00</div><div class="plan-dot" style="background:#d99b3d"></div><div class="plan-name">Memory Architecture quiz</div><div class="plan-duration">20 min</div></div><div class="plan-row"><div class="plan-time">15:30</div><div class="plan-dot" style="background:#cbd8d7"></div><div class="plan-name">Read chapter 4 notes</div><div class="plan-duration">30 min</div></div></div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="card"><div class="section-note" style="margin-bottom:16px">Evaluator Agent · confidence by topic</div>', unsafe_allow_html=True)
        for topic in TOPICS:
            st.markdown(f'<div class="topic-row"><div class="topic-line"><span>{topic["name"]}</span><span class="muted">{topic["score"]}%</span></div><div class="bar"><div class="bar-fill bar-{topic["color"]}" style="width:{topic["score"]}%"></div></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-head"><span class="section-title">Next up</span><span class="section-note">Recommendation Agent</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="next-card"><div><div class="eyebrow">Recommended focus · 20 minutes</div><div class="next-title">Practice Addressing Modes</div><div class="next-copy">You missed 3 questions here recently. A short focused quiz will strengthen the concept before your next study block.</div></div>', unsafe_allow_html=True)
    if st.button("Start focused quiz", type="primary", key="dashboard_quiz"):
        navigate("Quizzes")
    st.markdown('</div>', unsafe_allow_html=True)


def materials():
    header("Document Agent", "Your materials", "Upload notes and past papers. StudyPilot will organize the raw material for you.")
    agent_strip("Document")
    st.markdown('<div class="upload-zone"><div class="upload-icon">↑</div><div style="font-family:Manrope;font-weight:800;font-size:17px">Drop your study material here</div><div class="muted" style="font-size:12px;margin-top:7px">PDF, TXT or Markdown · up to 50 MB per file</div></div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Choose files", type=["pdf", "txt", "md"], accept_multiple_files=True, label_visibility="collapsed")
    if uploaded:
        files = []
        chunks = []
        for file in uploaded:
            try:
                extracted = extract_chunks(file)
                chunks.extend(extracted)
                suffix = Path(file.name).suffix.lower().replace(".", "").upper()
                label = "Past paper" if any(word in file.name.lower() for word in ["past", "exam", "paper", "question"]) else "Lecture notes"
                pages = max((chunk.get("page", 1) for chunk in extracted), default=1) if suffix == "PDF" else 1
                files.append({"name": file.name, "type": label, "pages": pages, "format": suffix})
            except (ValueError, ImportError) as error:
                st.error(f"Could not read {file.name}: {error}")
        st.session_state.files = files
        st.session_state.chunks = chunks
        if chunks:
            st.success(f"Document Agent ready · {len(chunks)} text chunks extracted")

    if st.session_state.files:
        st.markdown('<div class="section-head"><span class="section-title">Uploaded material</span><span class="section-note">Document Agent output</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        for file in st.session_state.files:
            st.markdown(f'<div class="file-row"><div class="file-icon">{file["format"]}</div><div class="file-name">{file["name"]}</div><div class="file-type">{file["type"]}</div><div class="file-pages">{file["pages"]} page' + ("s" if file["pages"] != 1 else "") + '</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("Review extracted topics", type="primary", key="materials_topics"):
            navigate("Topics")
    else:
        st.markdown('<div class="card" style="margin-top:20px;text-align:center;color:#6e7f82;font-size:13px">Your uploaded files will appear here with their detected type and page count.</div>', unsafe_allow_html=True)


def topics_page():
    header("Topic Agent", "The topics that matter", "These concepts were found across your uploaded material. Mark the ones most likely to appear in your exam.")
    agent_strip("Topics")
    st.markdown('<div class="card" style="margin-bottom:18px;display:flex;justify-content:space-between;align-items:center"><div><b>12 topics extracted</b><div class="muted" style="font-size:12px;margin-top:4px">Based on 4 study sources · last analyzed today</div></div><div style="color:#167c80;font-size:12px;font-weight:700">8 marked important</div></div>', unsafe_allow_html=True)
    for row in [TOPICS, [{"name": "CPU Architecture", "score": 76, "color": "good", "detail": "Strong", "concepts": ["ALU", "Control unit"]}, {"name": "Assembly Instructions", "score": 67, "color": "warn", "detail": "Making progress", "concepts": ["MOV", "ADD", "SUB"]}, {"name": "I/O Systems", "score": 44, "color": "risk", "detail": "Needs review", "concepts": ["Ports", "Interrupts"]}]]:
        cols = st.columns(3, gap="medium")
        for col, topic in zip(cols, row):
            with col:
                st.markdown(f'<div class="card topic-card"><div class="section-note">{topic["detail"]} · {topic["score"]}% confidence</div><div class="topic-card-title">{topic["name"]}</div><div class="bar"><div class="bar-fill bar-{topic["color"]}" style="width:{topic["score"]}%"></div></div><div style="margin-top:12px">' + ''.join(f'<span class="tag">{concept}</span>' for concept in topic["concepts"]) + '</div></div>', unsafe_allow_html=True)
                st.checkbox("Important for exam", value=st.session_state.important_topics.get(topic["name"], False), key=f"important_{topic['name']}")


def study_plan():
    header("Planner Agent", "Your study plan", "A realistic rhythm built around your exam date and the topics that need the most attention.")
    agent_strip("Planner")
    st.markdown('<div class="card" style="margin-bottom:22px"><div class="section-note">Exam countdown</div><div style="font-family:Manrope;font-size:28px;font-weight:800;margin-top:5px">18 days to go</div><div class="bar" style="margin-top:14px"><div class="bar-fill bar-good" style="width:42%"></div></div><div class="muted" style="font-size:12px;margin-top:8px">42% of your planned material covered</div></div>', unsafe_allow_html=True)
    for offset, title, items in [(0, "Today · Monday", [("09:00", "Review Addressing Modes", "45 min"), ("11:00", "Memory Architecture quiz", "20 min"), ("15:30", "Read chapter 4 notes", "30 min")]), (1, "Tuesday", [("09:00", "Assembly Instructions", "45 min"), ("11:00", "Practice past paper", "35 min")]), (2, "Wednesday", [("10:00", "CPU Architecture review", "40 min"), ("14:00", "Mixed topic quiz", "25 min")])]:
        st.markdown(f'<div class="section-head"><span class="section-title">{title}</span><span class="section-note">{date.today() + timedelta(days=offset)}</span></div><div class="card">', unsafe_allow_html=True)
        for time, title, duration in items:
            st.markdown(f'<div class="plan-row"><div class="plan-time">{time}</div><div class="plan-dot"></div><div class="plan-name">{title}</div><div class="plan-duration">{duration}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


def quizzes():
    questions = [
        ("Addressing Modes", "Which addressing mode places the actual operand value directly inside the instruction?", ["Immediate addressing", "Indirect addressing", "Register addressing", "Direct addressing"]),
        ("Memory Architecture", "Which type of memory loses its contents when power is removed?", ["ROM", "RAM", "Flash memory", "Cache" ]),
        ("Registers", "Which register normally points to the next instruction to execute?", ["EAX", "ESP", "EIP", "EBX"]),
    ]
    index = st.session_state.quiz_index % len(questions)
    topic, question, options = questions[index]
    header("Quiz Agent", "Focused practice", "One question at a time. Answer from memory, then use the explanation to close the gap.")
    agent_strip("Quiz")
    progress = (index + (1 if st.session_state.quiz_submitted else 0)) / len(questions)
    st.progress(progress, text=f"Question {index + 1} of {len(questions)}")
    st.markdown('<div class="card" style="margin-top:22px;padding:34px">', unsafe_allow_html=True)
    st.markdown(f'<div class="quiz-number">{topic} · 2 minutes</div><div class="quiz-question">{question}</div>', unsafe_allow_html=True)
    answer = st.radio("Choose one answer", options, key=f"answer_{index}", label_visibility="collapsed")
    if not st.session_state.quiz_submitted:
        if st.button("Submit answer", type="primary", key=f"submit_{index}"):
            st.session_state.quiz_answer = answer
            st.session_state.quiz_submitted = True
            st.rerun()
    else:
        correct = options[0] if index == 0 else options[1] if index == 1 else options[2]
        if answer == correct:
            st.success("Correct. You have this concept down.")
        else:
            st.warning(f"Not quite. The correct answer is {correct}.")
        if st.button("Next question", type="primary", key=f"next_{index}"):
            st.session_state.quiz_index += 1
            st.session_state.quiz_submitted = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def progress_page():
    header("Evaluator Agent", "Your progress", "See what is sticking, where confidence is slipping, and what StudyPilot recommends next.")
    agent_strip("Evaluate")
    top = st.columns([.6, 1.4], gap="large")
    with top[0]:
        st.markdown('<div class="card" style="text-align:center"><div class="score">68%</div><div class="score-label">overall readiness</div><div class="metric-foot">+8% since last week</div></div>', unsafe_allow_html=True)
    with top[1]:
        st.markdown('<div class="card"><div class="section-title">Topic confidence</div>', unsafe_allow_html=True)
        for topic in TOPICS + [{"name": "CPU Architecture", "score": 76, "color": "good"}]:
            st.markdown(f'<div class="topic-row"><div class="topic-line"><span>{topic["name"]}</span><span class="muted">{topic["score"]}%</span></div><div class="bar"><div class="bar-fill bar-{topic["color"]}" style="width:{topic["score"]}%"></div></div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><span class="section-title">Recommendation</span><span class="section-note">Based on your last 8 quizzes</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="next-card"><div><div class="eyebrow">Recommendation Agent</div><div class="next-title">Return to Addressing Modes</div><div class="next-copy">Your confidence is 38%, the lowest in the current topic set. Review the examples, then take a short 5-question quiz.</div></div>', unsafe_allow_html=True)
    if st.button("Review this topic", type="primary", key="progress_review"):
        navigate("Quizzes")
    st.markdown('</div>', unsafe_allow_html=True)


init_state()
render_sidebar()
page = st.session_state.page
if page == "Dashboard":
    dashboard()
elif page == "Materials":
    materials()
elif page == "Topics":
    topics_page()
elif page == "Study plan":
    study_plan()
elif page == "Quizzes":
    quizzes()
elif page == "Progress":
    progress_page()