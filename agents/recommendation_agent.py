from typing import Any


def calculate_overall_score(evaluation: list[dict[str, Any]]) -> float:
    """Calculate the student's overall score as a percentage."""

    if not evaluation:
        return 0.0

    total_score = sum(float(item.get("score", 0)) for item in evaluation)
    max_score = len(evaluation)

    return round((total_score / max_score) * 100, 2)


def calculate_topic_performance(
    evaluation: list[dict[str, Any]]
) -> dict[str, float]:
    """Calculate performance percentage for each topic."""

    topic_scores: dict[str, list[float]] = {}

    for item in evaluation:
        topic_id = item.get("topic_id")

        if not topic_id:
            continue

        score = float(item.get("score", 0))

        if topic_id not in topic_scores:
            topic_scores[topic_id] = []

        topic_scores[topic_id].append(score)

    topic_performance = {}

    for topic_id, scores in topic_scores.items():
        percentage = (sum(scores) / len(scores)) * 100
        topic_performance[topic_id] = round(percentage, 2)

    return topic_performance


def get_topic_name(
    topic_id: str,
    topics: list[dict[str, Any]]
) -> str:
    """Find a topic name using its topic ID."""

    for topic in topics:
        if topic.get("topic_id") == topic_id:
            return topic.get("topic", topic_id)

    return topic_id


def create_recommendation(
    evaluation: list[dict[str, Any]],
    weak_topics: list[str],
    topics: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Generate personalized study recommendations.

    Inputs:
        evaluation: Question-level evaluation results.
        weak_topics: Topic IDs identified as weak by the Evaluator Agent.
        topics: Topic information produced by the Topic Agent.

    Returns:
        A recommendation object.
    """

    overall_score = calculate_overall_score(evaluation)

    topic_performance = calculate_topic_performance(evaluation)

    recommendations = []

    for topic_id in weak_topics:
        topic_name = get_topic_name(topic_id, topics)

        performance = topic_performance.get(topic_id, 0)

        if performance < 50:
            priority = "high"
            action = "review_and_practice"
            reason = (
                f"Your performance in {topic_name} is {performance}%. "
                "Review the topic carefully and practice more questions."
            )

        else:
            priority = "medium"
            action = "review"
            reason = (
                f"Your performance in {topic_name} is {performance}%. "
                "Review the key concepts and practice additional questions."
            )

        recommendations.append(
            {
                "topic_id": topic_id,
                "topic": topic_name,
                "priority": priority,
                "action": action,
                "reason": reason,
            }
        )

    strong_topics = [
        topic_id
        for topic_id in topic_performance
        if topic_id not in weak_topics
    ]

    return {
        "overall_score": overall_score,
        "topic_performance": topic_performance,
        "weak_topics": weak_topics,
        "strong_topics": strong_topics,
        "recommendations": recommendations,
    }


def recommendation_agent(state: dict[str, Any]) -> dict[str, Any]:
    """
    Recommendation Agent entry point.

    Reads:
        evaluation
        weak_topics
        topics

    Writes:
        recommendation
    """

    evaluation = state.get("evaluation", [])
    weak_topics = state.get("weak_topics", [])
    topics = state.get("topics", [])

    recommendation = create_recommendation(
        evaluation=evaluation,
        weak_topics=weak_topics,
        topics=topics,
    )

    return {
        "recommendation": recommendation
    }