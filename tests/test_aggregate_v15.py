import pandas as pd

from analysis import aggregate_v15 as A


def test_periods_follow_timeline():
    ps = A.periods()
    assert A.period_of("2024-06-01", ps) == "before_plan"
    assert A.period_of("2024-11-01", ps) == "announced"
    assert A.period_of("2024-11-25", ps) == "law_in_force"
    assert A.period_of("2025-08-01", ps) == "struck_down"
    assert A.period_of("2026-09-30", ps) == "appeal_allowed"


def test_build_keeps_text_sources_apart():
    rows = []
    for i, ts in enumerate(["quoted", "newsroom"] * 4):
        r = {
            "sentence_id": f"s{i}",
            "article_id": f"a{i % 3}",
            "outlet": "ctv",
            "part": "body",
            "topic": "bike_lane",
            "period": "announced",
            "text_source": ts,
            "source_role": "resident" if ts == "quoted" else None,
            "loaded_language": 0.2,
        }
        for f in A.lfs_v15.FRAMES:
            r[f"frame_{f}"] = float(f == "safety")
        for lab in A.v15.TARGETS:
            for v in A.lfs_v15.V15_LABELS[lab][:2]:
                r[f"{lab}_{v}"] = 0.0
        rows.append(r)
    t = A.build(pd.DataFrame(rows))["v15_frames_by_source"]
    assert set(t.text_source) == {"quoted", "newsroom"}
    assert t[t.measure == "frame_safety"].rate.eq(1.0).all()


def test_attributed_newsroom_text_is_its_own_source():
    # codebook 9.2 (D-81): a source's position reported by the newsroom is not the outlet's
    assert A.text_source({"quoted": 1, "attributed": 1}, "quoted") == "quoted"
    assert A.text_source({"quoted": 0, "attributed": 1}, "newsroom") == "attributed"
    assert A.text_source({"quoted": 0, "attributed": 0}, "newsroom") == "newsroom"
