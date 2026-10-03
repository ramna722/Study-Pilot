"""
run_topic_agent.py  --  try the Topic Agent on a text file (uses your REAL API key).
Run:  python run_topic_agent.py
"""
from agents.topic_agent import run_topic_agent

with open("sample_data/sample_notes.txt", encoding="utf-8") as f:
    text = f.read()

# Stand-in for the Document Agent: split text into paragraphs ("chunks").
chunks = [p for p in text.split("\n\n") if p.strip()]

topics = run_topic_agent(chunks)
for t in topics:
    print(f"[{t['importance']}] {t['topic']}  (mentions: {t['mentions']})")
    print("   ", t["summary"])
    print("    concepts:", ", ".join(t["key_concepts"]))
