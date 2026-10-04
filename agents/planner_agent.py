from datetime import date, timedelta
from typing import Any


IMPORTANCE_WEIGHT = {
    "High": 3,
    "Medium": 2,
    "Low": 1,
}


def parse_date(value: str | date) -> date:
    """Convert a date string into a date object."""

    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        raise ValueError("exam_date must be a YYYY-MM-DD string or date object.")

    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("exam_date must use YYYY-MM-DD format.")


def validate_topics(topics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate and clean the topics received from the Topic Agent."""

    if not isinstance(topics, list):
        raise ValueError("topics must be a list.")

    valid_topics = []

    for topic in topics:
        if not isinstance(topic, dict):
            continue

        topic_id = topic.get("id")
        topic_name = topic.get("topic")

        if not topic_id or not topic_name:
            continue

        importance = topic.get("importance", "Medium")

        if importance not in IMPORTANCE_WEIGHT:
            importance = "Medium"

        key_concepts = topic.get("key_concepts", [])

        if not isinstance(key_concepts, list):
            key_concepts = []

        valid_topics.append(
            {
                "id": str(topic_id),
                "topic": str(topic_name),
                "importance": importance,
                "summary": str(topic.get("summary", "")).strip(),
                "key_concepts": [
                    str(concept).strip()
                    for concept in key_concepts
                    if str(concept).strip()
                ],
                "mentions": topic.get("mentions", 0),
            }
        )

    return valid_topics


def calculate_study_days(
    start_date: date,
    exam_date: date,
) -> int:
    """
    Calculate the number of available study days.

    The exam date itself is not counted as a study day.
    """

    days = (exam_date - start_date).days

    if days <= 0:
        raise ValueError("exam_date must be after the start date.")

    return days


def calculate_topic_hours(
    topics: list[dict[str, Any]],
    total_hours: float,
) -> dict[str, float]:
    """
    Allocate total study hours according to topic importance.

    High = 3 weight
    Medium = 2 weight
    Low = 1 weight
    """

    if not topics:
        return {}

    total_weight = sum(
        IMPORTANCE_WEIGHT.get(topic["importance"], 1)
        for topic in topics
    )

    if total_weight == 0:
        return {}

    topic_hours = {}

    for topic in topics:
        weight = IMPORTANCE_WEIGHT.get(topic["importance"], 1)

        hours = (weight / total_weight) * total_hours

        topic_hours[topic["id"]] = round(hours, 2)

    return topic_hours


def build_daily_plan(
    topics: list[dict[str, Any]],
    topic_hours: dict[str, float],
    start_date: date,
    study_days: int,
    daily_hours: float,
) -> list[dict[str, Any]]:
    """
    Distribute topic study time across the available study days.

    Topics are processed according to importance, while keeping
    each day's total study time within daily_hours.
    """

    remaining_hours = {
        topic["id"]: topic_hours.get(topic["id"], 0)
        for topic in topics
    }

    topic_lookup = {
        topic["id"]: topic
        for topic in topics
    }

    days = []

    for day_number in range(1, study_days + 1):
        current_date = start_date + timedelta(days=day_number - 1)

        available_hours = daily_hours
        planned_topics = []

        for topic in topics:
            topic_id = topic["id"]
            remaining = remaining_hours[topic_id]

            if remaining <= 0:
                continue

            if available_hours <= 0:
                break

            allocated = min(remaining, available_hours)

            allocated = round(allocated, 2)

            if allocated <= 0:
                continue

            topic_data = topic_lookup[topic_id]

            planned_topics.append(
                {
                    "topic_id": topic_id,
                    "topic": topic_data["topic"],
                    "importance": topic_data["importance"],
                    "hours": allocated,
                    "key_concepts": topic_data["key_concepts"],
                }
            )

            remaining_hours[topic_id] = round(
                remaining - allocated,
                2
            )

            available_hours = round(
                available_hours - allocated,
                2
            )

        days.append(
            {
                "day": day_number,
                "date": current_date.isoformat(),
                "topics": planned_topics,
                "total_hours": round(
                    daily_hours - available_hours,
                    2
                ),
            }
        )

    return days


def get_unscheduled_topics(
    topics: list[dict[str, Any]],
    topic_hours: dict[str, float],
    days: list[dict[str, Any]],
) -> list[str]:
    """Return topic IDs that could not receive study time."""

    scheduled_hours = {}

    for day in days:
        for planned_topic in day["topics"]:
            topic_id = planned_topic["topic_id"]

            scheduled_hours[topic_id] = (
                scheduled_hours.get(topic_id, 0)
                + planned_topic["hours"]
            )

    unscheduled = []

    for topic in topics:
        topic_id = topic["id"]
        required = topic_hours.get(topic_id, 0)
        scheduled = scheduled_hours.get(topic_id, 0)

        if scheduled + 0.01 < required:
            unscheduled.append(topic_id)

    return unscheduled


def create_study_plan(
    topics: list[dict[str, Any]],
    exam_date: str | date,
    daily_hours: float,
    start_date: str | date | None = None,
) -> dict[str, Any]:
    """
    Create a complete study plan.

    Inputs:
        topics:
            Topics produced by the Topic Agent.

        exam_date:
            Student's exam date in YYYY-MM-DD format.

        daily_hours:
            Number of hours the student can study each day.

        start_date:
            Optional starting date. Defaults to today.
            This parameter is mainly useful for testing.

    Returns:
        A study_plan dictionary.
    """

    if not isinstance(daily_hours, (int, float)):
        raise ValueError("daily_hours must be a number.")

    if daily_hours <= 0:
        raise ValueError("daily_hours must be greater than 0.")

    if start_date is None:
        start = date.today()
    else:
        start = parse_date(start_date)

    exam = parse_date(exam_date)

    study_days = calculate_study_days(
        start_date=start,
        exam_date=exam,
    )

    clean_topics = validate_topics(topics)

    if not clean_topics:
        return {
            "exam_date": exam.isoformat(),
            "daily_hours": float(daily_hours),
            "total_days": study_days,
            "total_hours": round(study_days * daily_hours, 2),
            "days": [],
            "unscheduled_topics": [],
        }

    total_hours = study_days * float(daily_hours)

    topic_hours = calculate_topic_hours(
        topics=clean_topics,
        total_hours=total_hours,
    )

    days = build_daily_plan(
        topics=clean_topics,
        topic_hours=topic_hours,
        start_date=start,
        study_days=study_days,
        daily_hours=float(daily_hours),
    )

    unscheduled_topics = get_unscheduled_topics(
        topics=clean_topics,
        topic_hours=topic_hours,
        days=days,
    )

    return {
        "exam_date": exam.isoformat(),
        "daily_hours": float(daily_hours),
        "total_days": study_days,
        "total_hours": round(total_hours, 2),
        "days": days,
        "unscheduled_topics": unscheduled_topics,
    }


def planner_agent_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    Planner Agent entry point for the shared StudyPilot state.

    Reads:
        state["topics"]
        state["exam_date"]
        state["daily_hours"]

    Writes:
        state["study_plan"]
    """

    if "topics" not in state:
        raise ValueError(
            "state has no 'topics'. The Topic Agent must run first."
        )

    if "exam_date" not in state:
        raise ValueError(
            "state has no 'exam_date'."
        )

    if "daily_hours" not in state:
        raise ValueError(
            "state has no 'daily_hours'."
        )

    state["study_plan"] = create_study_plan(
        topics=state["topics"],
        exam_date=state["exam_date"],
        daily_hours=state["daily_hours"],
    )

    return state