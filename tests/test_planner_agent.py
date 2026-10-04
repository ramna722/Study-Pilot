from datetime import date
import pytest

from agents.planner_agent import (
    calculate_study_days,
    calculate_topic_hours,
    create_study_plan,
    planner_agent_node,
)


TOPICS = [
    {
        "id": "t1",
        "topic": "CPU Components",
        "importance": "High",
        "summary": "The main components of a CPU.",
        "key_concepts": ["ALU", "Control Unit"],
        "mentions": 1,
    },
    {
        "id": "t2",
        "topic": "Registers",
        "importance": "High",
        "summary": "Fast storage inside the CPU.",
        "key_concepts": ["Stack pointer", "Instruction pointer"],
        "mentions": 1,
    },
    {
        "id": "t3",
        "topic": "Addressing Modes",
        "importance": "Medium",
        "summary": "Ways instructions locate operands.",
        "key_concepts": [
            "Immediate addressing",
            "Register addressing",
        ],
        "mentions": 1,
    },
]


def test_calculate_study_days():
    start = date(2026, 10, 4)
    exam = date(2026, 10, 10)

    result = calculate_study_days(start, exam)

    assert result == 6


def test_calculate_topic_hours():
    topics = [
        {
            "id": "t1",
            "topic": "CPU",
            "importance": "High",
        },
        {
            "id": "t2",
            "topic": "Memory",
            "importance": "Medium",
        },
        {
            "id": "t3",
            "topic": "I/O",
            "importance": "Low",
        },
    ]

    result = calculate_topic_hours(
        topics=topics,
        total_hours=6,
    )

    assert result["t1"] == 3.0
    assert result["t2"] == 2.0
    assert result["t3"] == 1.0


def test_create_study_plan():
    result = create_study_plan(
        topics=TOPICS,
        exam_date="2026-10-10",
        daily_hours=2,
        start_date="2026-10-04",
    )

    assert result["exam_date"] == "2026-10-10"
    assert result["daily_hours"] == 2.0
    assert result["total_days"] == 6
    assert result["total_hours"] == 12.0

    assert len(result["days"]) == 6


def test_daily_hours_are_not_exceeded():
    result = create_study_plan(
        topics=TOPICS,
        exam_date="2026-10-10",
        daily_hours=2,
        start_date="2026-10-04",
    )

    for day in result["days"]:
        assert day["total_hours"] <= 2.0


def test_topic_ids_are_preserved():
    result = create_study_plan(
        topics=TOPICS,
        exam_date="2026-10-10",
        daily_hours=2,
        start_date="2026-10-04",
    )

    scheduled_ids = set()

    for day in result["days"]:
        for topic in day["topics"]:
            scheduled_ids.add(topic["topic_id"])

    assert scheduled_ids == {"t1", "t2", "t3"}


def test_high_priority_topics_get_more_time():
    result = create_study_plan(
        topics=TOPICS,
        exam_date="2026-10-10",
        daily_hours=2,
        start_date="2026-10-04",
    )

    topic_hours = {}

    for day in result["days"]:
        for topic in day["topics"]:
            topic_id = topic["topic_id"]

            topic_hours[topic_id] = (
                topic_hours.get(topic_id, 0)
                + topic["hours"]
            )

    assert topic_hours["t1"] > topic_hours["t3"]
    assert topic_hours["t2"] > topic_hours["t3"]


def test_key_concepts_are_kept():
    result = create_study_plan(
        topics=TOPICS,
        exam_date="2026-10-10",
        daily_hours=2,
        start_date="2026-10-04",
    )

    planned_topics = []

    for day in result["days"]:
        planned_topics.extend(day["topics"])

    cpu_plan = next(
        topic
        for topic in planned_topics
        if topic["topic_id"] == "t1"
    )

    assert cpu_plan["key_concepts"] == [
        "ALU",
        "Control Unit",
    ]


def test_planner_agent_node():
    state = {
        "topics": TOPICS,
        "exam_date": "2026-10-10",
        "daily_hours": 2,
    }

    result = planner_agent_node(state)

    assert "study_plan" in result

    assert result["study_plan"]["exam_date"] == "2026-10-10"
    assert result["study_plan"]["daily_hours"] == 2.0
    assert result["study_plan"]["total_days"] == 6


def test_empty_topics():
    result = create_study_plan(
        topics=[],
        exam_date="2026-10-10",
        daily_hours=2,
        start_date="2026-10-04",
    )

    assert result["total_days"] == 6
    assert result["total_hours"] == 12.0
    assert result["days"] == []
    assert result["unscheduled_topics"] == []


def test_invalid_daily_hours():
    with pytest.raises(ValueError):
        create_study_plan(
            topics=TOPICS,
            exam_date="2026-10-10",
            daily_hours=0,
            start_date="2026-10-04",
        )


def test_invalid_exam_date():
    with pytest.raises(ValueError):
        create_study_plan(
            topics=TOPICS,
            exam_date="2026-10-03",
            daily_hours=2,
            start_date="2026-10-04",
        )