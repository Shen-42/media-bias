from eval.triage import count


def test_count_disagreements_ignores_abstains():
    votes = {
        "voice": {"rule": "active", "nli": "active", "qwen": None},
        "focus": {"rule": "vru", "nli": "driver", "qwen": "vru"},
        "accident_term": {"rule": "false", "nli": "true", "qwen": "true"},
    }
    assert count(votes) == 2
    assert count({"voice": {"rule": "active", "nli": None}}) == 0
