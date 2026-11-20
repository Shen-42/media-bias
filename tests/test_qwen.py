from nlp.labeling.qwen import TASKS, schema, validate


def test_schema_lists_only_codebook_values():
    s = schema("crash")["properties"]["items"]["items"]["properties"]
    assert s["voice"]["enum"] == [
        "active",
        "passive_with_agent",
        "agentless_passive",
        "intransitive",
        "nominal",
    ]
    assert s["vru_as_actor"]["type"] == "boolean"
    assert set(schema("context")["properties"]["items"]["items"]["required"]) == {
        "id",
        "vru_conduct_detail",
        "thematic_cue",
    }


def test_invalid_output_is_abstain():
    rec = validate("crash", {"voice": "passive", "focus": "vru", "vru_as_actor": "yes"})
    assert rec["voice"] is None  # not a codebook value
    assert rec["focus"] == "vru"
    assert rec["vru_as_actor"] is None  # string, not boolean
    assert rec["driver_reference"] is None  # missing


def test_valid_boolean_output():
    assert validate("context", {"vru_conduct_detail": True, "thematic_cue": False}) == {
        "vru_conduct_detail": "true",
        "thematic_cue": "false",
    }


def test_tasks_cover_all_labels():
    labels = {k for t in TASKS.values() for k in t["fields"]}
    assert labels == {
        "voice",
        "driver_reference",
        "focus",
        "vru_as_actor",
        "accident_term",
        "vru_conduct_detail",
        "thematic_cue",
        "policy_frame",
        "stance_infrastructure",
        "stance_cyclists",
        "stance_transit",
    }


def test_v15_task_matches_codebook_values():
    from nlp.labeling.lfs_v15 import V15_LABELS

    assert TASKS["v15"]["fields"] == V15_LABELS
