from nlp.labeling import lfs_v15 as L


def x(text, quoted=False, attributed=False, nli=None, qwen=None):
    return {"text": text, "quoted": quoted, "attributed": attributed, "nli": nli, "qwen": qwen}


def test_frame_lexicon_positive_and_negative():
    assert L.lf_frame_lexicon(x("Removing the lanes will cost the province $48 million.")) == (
        "economic"
    )
    assert L.lf_frame_lexicon(x("The court ruled that the removal violates the Charter.")) == (
        "legality"
    )
    assert L.lf_frame_lexicon(x("Drivers say the commute now takes 20 minutes longer.")) == (
        "quality_of_life"
    )
    assert L.lf_frame_lexicon(x("A poll found 55 per cent of residents support the plan.")) == (
        "other"
    )
    assert L.lf_frame_lexicon(x("The agency ordered a review of its maintenance records.")) == (
        "other"
    )
    assert L.lf_frame_lexicon(x("She spoke at a news conference.")) is None
    # two frames: abstain rather than guess
    assert L.lf_frame_lexicon(x("The court case has cost $2 million.")) is None


def test_frame_schedule_none():
    assert L.lf_frame_schedule_none(x("Work begins Monday at 7 a.m.")) == "none"
    assert L.lf_frame_schedule_none(x("Work begins Monday and will cost $5 million.")) is None


def test_no_target_means_none():
    assert L.lf_infra_no_target(x("Buses were delayed by 20 minutes.")) == "none"
    assert L.lf_infra_no_target(x("The bike lanes cost $5 million.")) is None
    assert L.lf_cyclists_no_target(x("Council will vote Thursday.")) == "none"
    assert L.lf_transit_no_target(x("The bike lanes opened in 2023.")) == "none"


def test_attributed_position_counts_as_stance():
    # codebook 9.2 (D-81): a source's stated position is stance, even outside quotes
    s = "The province says the lanes have been a disaster for local shops."
    assert L.lf_infra_cues(x(s, attributed=True)) == "oppose"
    assert L.lf_transit_cues(
        x("The mayor said she supports the subway extension.", attributed=True)
    ) == ("support")
    # a plan with no evaluation stays unlabeled
    assert L.lf_infra_cues(x("The province plans to remove the lanes.", attributed=True)) is None


def test_stance_cues_are_symmetric():
    assert L.lf_infra_cues(x('"These lanes save lives," a cyclist said.', quoted=True)) == (
        "support"
    )
    assert L.lf_infra_cues(
        x('"The lanes have choked this street," a driver said.', quoted=True)
    ) == ("oppose")
    assert L.lf_infra_cues(x("The lanes cost $5 million.")) is None
    assert L.lf_cyclists_cues(x("Most cyclists follow the rules.")) == "positive"
    assert L.lf_cyclists_cues(x("Cyclists blow through red lights here every day.")) == "negative"
    assert L.lf_transit_cues(x('"This subway is a waste of money," she said.', quoted=True)) == (
        "oppose"
    )


def test_nli_and_qwen_lfs():
    assert L.lf_infra_nli(x("t", nli={"support": 0.9, "oppose": 0.05, "none": 0.05})) == "support"
    assert L.lf_infra_nli(x("t", nli={"support": 0.5, "oppose": 0.3, "none": 0.2})) is None
    assert L.lf_frame_qwen(x("t", qwen="safety")) == "safety"
    assert L.lf_frame_qwen(x("t")) is None


def test_every_lf_returns_codebook_value_or_abstain():
    s = [x("The bike lanes have been a disaster for local shops, the BIA said.", attributed=True)]
    for label, fns in L.LFS.items():
        for fn in fns:
            for item in s:
                assert fn(item) in L.V15_LABELS[label] + [None]
