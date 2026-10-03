"""
Tests for the Topic Agent. They use a FAKE AI, so no API key is needed.
Run:  python tests/test_topic_agent.py      (or: pytest)
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.topic_agent import run_topic_agent, parse_json, topic_agent_node


def fake_llm(prompt, system=""):
    """Pretends to be the AI. Wraps the JSON in ```json fences, like real AIs often do."""
    reply = {"topics": [
        {"topic": "CPU Architecture", "importance": "High",
         "summary": "Parts of the CPU.", "key_concepts": ["ALU", "Control Unit"]},
        {"topic": "Registers", "importance": "High",
         "summary": "Fast storage in the CPU.", "key_concepts": ["EAX", "EBX"]},
        {"topic": "bad topic", "importance": "SUPER", "key_concepts": "oops"},
    ]}
    return "```json\n" + json.dumps(reply) + "\n```"


def test_parse_json_handles_messy_reply():
    assert parse_json('Sure! {"a": 1} hope that helps') == {"a": 1}
    assert parse_json("not json at all") is None


def test_topic_agent_output_shape():
    chunks = ["CPU consists of ALU, Control Unit and registers.", "Registers are storage."]
    topics = run_topic_agent(chunks, llm_fn=fake_llm)
    assert len(topics) == 3
    for t in topics:
        assert set(t) == {"id", "topic", "importance", "summary", "key_concepts", "mentions"}
        assert t["importance"] in ("High", "Medium", "Low")
    assert topics[0]["id"] == "t1"


def test_works_inside_the_shared_state():
    state = {"chunks": [{"text": "Registers are storage.", "page": 1}]}  # dict chunks are OK
    state = topic_agent_node(state, llm_fn=fake_llm)
    assert len(state["topics"]) == 3


if __name__ == "__main__":
    test_parse_json_handles_messy_reply()
    test_topic_agent_output_shape()
    test_works_inside_the_shared_state()
    print("All tests passed ✅")
    for t in run_topic_agent(["CPU consists of ALU."], llm_fn=fake_llm):
        print(f"[{t['importance']}] {t['topic']}")
