import pandas as pd

from eval.polnear_check import cue_spans, label_sentences, metrics, sentence_spans

ANN = "T1\tSource 0 3\tShe\nT2\tCue 4 8\tsaid\nT3\tCue 20 24;30 34\tx y\nE1\tAttribution:T2"


def test_cue_spans_reads_only_cues_and_splits_discontinuous_spans():
    assert cue_spans(ANN) == [(4, 8), (20, 24), (30, 34)]


def test_sentence_spans_from_corenlp_offsets():
    xml = (
        "<root><sentence id='1'><token><CharacterOffsetBegin>0</CharacterOffsetBegin>"
        "<CharacterOffsetEnd>3</CharacterOffsetEnd></token><token><CharacterOffsetBegin>4"
        "</CharacterOffsetBegin><CharacterOffsetEnd>9</CharacterOffsetEnd></token></sentence></root>"
    )
    assert sentence_spans(xml) == [(0, 9)]


def test_label_sentences_skips_quoted_and_marks_gold_and_pred():
    text = "She said no. The sky is blue. “All of this is quoted.”"
    sents = [(0, 12), (13, 29), (30, 54)]
    rows = label_sentences(text, sents, [(4, 8)])
    assert rows == [{"gold": True, "pred": True}, {"gold": False, "pred": False}]


def test_metrics_precision_and_recall():
    df = pd.DataFrame({"gold": [True, True, False], "pred": [True, False, True]})
    m = metrics(df)
    assert m["precision"] == 0.5 and m["recall"] == 0.5
