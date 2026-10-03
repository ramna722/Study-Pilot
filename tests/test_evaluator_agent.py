import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from agents.evaluator_agent import run_evaluator_agent, evaluator_agent_node

# Mock LLM function for tests
def mock_llm_correct(prompt, system):
    return '{"evaluation": "correct", "score": 1, "explanation": "Good job.", "needs_improvement": false}'

def mock_llm_incorrect(prompt, system):
    return '{"evaluation": "incorrect", "score": 0, "explanation": "Wrong.", "needs_improvement": true}'

def mock_llm_partially_correct(prompt, system):
    return '{"evaluation": "partially_correct", "score": 0, "explanation": "Half right.", "needs_improvement": true}'

def mock_llm_broken(prompt, system):
    return 'not a json'

def test_run_evaluator_agent_correct():
    student_answers = [{"question_id": 1, "student_answer": "RAM is temporary"}]
    questions = [{"question_id": 1, "question": "What is RAM?", "expected_answer": "Temporary memory", "topic_id": "t1"}]
    
    evals, weak = run_evaluator_agent(student_answers, questions, llm_fn=mock_llm_correct)
    
    assert len(evals) == 1
    assert evals[0]["question_id"] == 1
    assert evals[0]["topic_id"] == "t1"
    assert evals[0]["evaluation"] == "correct"
    assert len(weak) == 0

def test_run_evaluator_agent_incorrect_weak_topics():
    student_answers = [
        {"question_id": 1, "student_answer": "RAM is permanent"},
        {"question_id": 2, "student_answer": "CPU is central"}
    ]
    questions = [
        {"question_id": 1, "question": "What is RAM?", "expected_answer": "Temporary memory", "topic_id": "t1"},
        {"question_id": 2, "question": "What is CPU?", "expected_answer": "Central processing unit", "topic_id": "t2"}
    ]
    
    def dynamic_llm(prompt, system):
        if "Question ID: 1" in prompt:
            return mock_llm_incorrect(prompt, system)
        return mock_llm_correct(prompt, system)
        
    evals, weak = run_evaluator_agent(student_answers, questions, llm_fn=dynamic_llm)
    
    assert len(evals) == 2
    assert "t1" in weak
    assert "t2" not in weak
    assert len(weak) == 1

def test_missing_question_id():
    student_answers = [{"student_answer": "RAM is temporary"}]
    questions = [{"question_id": 1, "question": "What is RAM?", "expected_answer": "Temporary memory", "topic_id": "t1"}]
    
    evals, weak = run_evaluator_agent(student_answers, questions, llm_fn=mock_llm_correct)
    assert len(evals) == 0
    assert len(weak) == 0

def test_mismatched_question_id():
    student_answers = [{"question_id": 99, "student_answer": "RAM is temporary"}]
    questions = [{"question_id": 1, "question": "What is RAM?", "expected_answer": "Temporary memory", "topic_id": "t1"}]
    
    evals, weak = run_evaluator_agent(student_answers, questions, llm_fn=mock_llm_correct)
    assert len(evals) == 0

def test_llm_fallback():
    student_answers = [{"question_id": 1, "student_answer": "RAM is temporary"}]
    questions = [{"question_id": 1, "question": "What is RAM?", "expected_answer": "Temporary memory", "topic_id": "t1"}]
    
    evals, weak = run_evaluator_agent(student_answers, questions, llm_fn=mock_llm_broken)
    
    assert len(evals) == 1
    assert evals[0]["evaluation"] == "incorrect"
    assert "t1" in weak

def test_evaluator_agent_node():
    state = {
        "student_answers": [{"question_id": 1, "student_answer": "RAM is temporary"}],
        "questions": [{"question_id": 1, "question": "What is RAM?", "expected_answer": "Temporary memory", "topic_id": "t1"}]
    }
    
    new_state = evaluator_agent_node(state, llm_fn=mock_llm_partially_correct)
    
    assert "evaluation" in new_state
    assert "weak_topics" in new_state
    assert new_state["evaluation"][0]["evaluation"] == "partially_correct"
    assert new_state["weak_topics"] == ["t1"]

def test_evaluator_agent_node_empty_state():
    state = {}
    new_state = evaluator_agent_node(state, llm_fn=mock_llm_correct)
    assert new_state["evaluation"] == []
    assert new_state["weak_topics"] == []

