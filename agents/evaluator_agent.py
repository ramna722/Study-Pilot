"""
agents/evaluator_agent.py  --  the EVALUATOR AGENT

Job: read student answers and questions, evaluate correctness, and identify weak topics.

Input state keys:
- 'questions': list of dicts [{"question_id": 1, "question": "...", "expected_answer": "...", "topic_id": "t1"}]
- 'student_answers': list of dicts [{"question_id": 1, "student_answer": "..."}]

Output state keys:
- 'evaluation': list of dicts [{"question_id": 1, "evaluation": "correct", "score": 1, "explanation": "...", "topic_id": "t1", "needs_improvement": False}]
- 'weak_topics': list of strings ["t1", "t3"]
"""
import json
import logging
from core.llm import ask_llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert tutor evaluating a student's answer to a quiz question. "
    "Evaluate the student's answer based on semantic correctness, not exact string matching. "
    "Always respond with a valid JSON object."
)

PROMPT_TEMPLATE = """
Question ID: {question_id}
Question: {question}
Expected Answer: {expected_answer}
Student Answer: {student_answer}

Evaluate the student's answer and return a JSON object with the following fields:
- question_id: The exact same question ID provided in the input ({question_id}).
- evaluation: "correct", "partially_correct", or "incorrect"
- score: integer 0 or 1 (1 for correct, 0 for incorrect/partially_correct).
- explanation: Why the student's answer is correct or incorrect.
- needs_improvement: boolean (true if evaluation is not 'correct')
"""

def parse_llm_json(text):
    import re
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return None

def evaluate_single_answer(student_ans, question_info, llm_fn=ask_llm):
    q_id = student_ans.get("question_id")
    # Graceful handling of missing data
    if q_id is None or "student_answer" not in student_ans or not question_info:
        return None
        
    prompt = PROMPT_TEMPLATE.format(
        question_id=q_id,
        question=question_info.get("question", ""),
        expected_answer=question_info.get("expected_answer", ""),
        student_answer=student_ans.get("student_answer", "")
    )
    
    for _ in range(2):
        response_text = llm_fn(prompt, SYSTEM_PROMPT)
        data = parse_llm_json(response_text)
        if isinstance(data, dict) and "evaluation" in data:
            # Ensure topic_id and question_id are preserved
            data["question_id"] = q_id
            data["topic_id"] = question_info.get("topic_id")
            # Ensure defaults
            if "score" not in data:
                data["score"] = 1 if data.get("evaluation") == "correct" else 0
            if "needs_improvement" not in data:
                data["needs_improvement"] = data.get("evaluation") != "correct"
            return data
            
    # Fallback if LLM fails completely
    return {
        "question_id": q_id,
        "evaluation": "incorrect",
        "score": 0,
        "explanation": "Failed to evaluate answer.",
        "topic_id": question_info.get("topic_id"),
        "needs_improvement": True
    }

def run_evaluator_agent(student_answers, questions, llm_fn=ask_llm):
    evaluations = []
    weak_topics = set()
    
    # Map questions by ID for easy lookup
    q_map = {q.get("question_id"): q for q in questions if isinstance(q, dict)}
    
    for ans in student_answers:
        if not isinstance(ans, dict):
            continue
            
        q_id = ans.get("question_id")
        if q_id not in q_map:
            continue
            
        q_info = q_map[q_id]
        eval_result = evaluate_single_answer(ans, q_info, llm_fn)
        
        if eval_result:
            evaluations.append(eval_result)
            
            # Rule: consider a topic weak when at least one answered question for that topic is incorrect or partially_correct.
            if eval_result.get("evaluation") in ["incorrect", "partially_correct"]:
                topic_id = eval_result.get("topic_id")
                if topic_id:
                    weak_topics.add(topic_id)
                    
    return evaluations, list(weak_topics)

def evaluator_agent_node(state, llm_fn=ask_llm):
    student_answers = state.get("student_answers", [])
    questions = state.get("questions", [])
    
    if not student_answers or not questions:
        state["evaluation"] = []
        state["weak_topics"] = []
        return state
        
    evaluations, weak_topics = run_evaluator_agent(student_answers, questions, llm_fn=llm_fn)
    state["evaluation"] = evaluations
    state["weak_topics"] = weak_topics
    return state

