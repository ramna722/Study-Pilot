"""
topic_demo.py  --  a tiny Streamlit page to demo the Topic Agent.
Run:  streamlit run topic_demo.py
"""
import streamlit as st
from agents.topic_agent import run_topic_agent

st.title("🧠 StudyPilot: Topic Agent")
text = st.text_area("Paste your lecture notes here", height=250)
uploaded = st.file_uploader("...or upload a .txt file", type=["txt"])
if uploaded:
    text = uploaded.read().decode("utf-8", errors="ignore")

if st.button("Find important topics") and text.strip():
    chunks = [p for p in text.split("\n\n") if p.strip()]
    with st.spinner("Reading your notes..."):
        topics = run_topic_agent(chunks)
    for t in topics:
        st.subheader(f"{t['topic']}  ·  {t['importance']}")
        st.write(t["summary"])
        st.caption("Key concepts: " + ", ".join(t["key_concepts"]))
    with st.expander("Raw output (what the Planner Agent receives)"):
        st.json(topics)
