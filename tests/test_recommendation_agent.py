from agents.recommendation_agent import (
    calculate_overall_score,
    calculate_topic_performance,
    create_recommendation,
    recommendation_agent,
)


def test_calculate_overall_score():
    evaluation = [
        {
            "question_id": 1,
            "score": 1,
            "topic_id": "t1",
        },
        {
            "question_id": 2,
            "score": 0,
            "topic_id": "t2",
        },
        {
            "question_id": 3,
            "score": 1,
            "topic_id": "t1",
        },
    ]

    result = calculate_overall_score(evaluation)

    assert result == 66.67


def test_calculate_topic_performance():
    evaluation = [
        {
            "question_id": 1,
            "score": 1,
            "topic_id": "t1",
        },
        {
            "question_id": 2,
            "score": 0,
            "topic_id": "t2",
        },
        {
            "question_id": 3,
            "score": 1,
            "topic_id": "t1",
        },
        {
            "question_id": 4,
            "score": 0,
            "topic_id": "t2",
        },
    ]

    result = calculate_topic_performance(evaluation)

    assert result == {
        "t1": 100.0,
        "t2": 0.0,
    }


def test_create_recommendation():
    evaluation = [
        {
            "question_id": 1,
            "score": 1,
            "topic_id": "t1",
        },
        {
            "question_id": 2,
            "score": 0,
            "topic_id": "t2",
        },
    ]

    weak_topics = ["t2"]

    topics = [
        {
            "topic_id": "t1",
            "topic": "CPU",
        },
        {
            "topic_id": "t2",
            "topic": "Memory",
        },
    ]

    result = create_recommendation(
        evaluation=evaluation,
        weak_topics=weak_topics,
        topics=topics,
    )

    assert result["overall_score"] == 50.0
    assert result["topic_performance"]["t1"] == 100.0
    assert result["topic_performance"]["t2"] == 0.0
    assert result["weak_topics"] == ["t2"]

    assert len(result["recommendations"]) == 1
    assert result["recommendations"][0]["topic_id"] == "t2"
    assert result["recommendations"][0]["topic"] == "Memory"
    assert result["recommendations"][0]["priority"] == "high"


def test_recommendation_agent():
    state = {
        "topics": [
            {
                "topic_id": "t1",
                "topic": "CPU",
            },
            {
                "topic_id": "t2",
                "topic": "Memory",
            },
        ],
        "evaluation": [
            {
                "question_id": 1,
                "score": 1,
                "topic_id": "t1",
            },
            {
                "question_id": 2,
                "score": 0,
                "topic_id": "t2",
            },
        ],
        "weak_topics": ["t2"],
    }

    result = recommendation_agent(state)

    assert "recommendation" in result

    recommendation = result["recommendation"]

    assert recommendation["overall_score"] == 50.0
    assert recommendation["weak_topics"] == ["t2"]
    assert recommendation["strong_topics"] == ["t1"]

    assert recommendation["recommendations"][0]["topic"] == "Memory"


def test_empty_evaluation():
    state = {
        "topics": [],
        "evaluation": [],
        "weak_topics": [],
    }

    result = recommendation_agent(state)

    assert result["recommendation"]["overall_score"] == 0.0
    assert result["recommendation"]["topic_performance"] == {}
    assert result["recommendation"]["recommendations"] == []