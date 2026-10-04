# 🎓 StudyPilot

Multi-agent AI study assistant. Upload your notes, find important topics,
get a study plan, practice quizzes, and know what to study next.
(HEC + PakAngels Cohort 11 hackathon)

## Features
- Upload lecture notes, PDFs, past papers
- Find important topics automatically
- Personalized study plan
- Practice quizzes with answer checking
- Weak-topic recommendations

## Workflow
Student → Document → Topic → Planner → Quiz → Evaluator → Recommendation
(Weak topics found → more quiz questions → repeat)

## Agents
| Agent | File |
|---|---|
| Document | agents/document_agent.py |
| Topic | agents/topic_agent.py |
| Planner | agents/planner_agent.py |
| Quiz | agents/quiz_agent.py |
| Evaluator | agents/evaluator_agent.py |
| Recommendation | agents/recommendation_agent.py |

## Shared state names (all agents use these)
chunks, topics, study_plan, questions, student_answers,
evaluation, weak_topics, recommendation

The Document Agent accepts text, `.txt`/`.md` files, and PDFs. It writes
bounded text chunks with source and page metadata to `state["chunks"]`.

## Setup
    pip install -r requirements.txt
    copy .env.example .env     (then paste your Gemini key inside .env)

## Run
    python run_topic_agent.py
    streamlit run app.py

## Team rules
- Work on your own branch and your own agent file.
- Never upload `.env` or API keys.
- Tell the group before changing core/llm.py or requirements.txt.
