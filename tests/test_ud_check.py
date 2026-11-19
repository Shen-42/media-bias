import pandas as pd

from eval.ud_check import gold_passive_offsets, metrics


def test_gold_passive_offsets():
    text = "He was hit by a car and has left."
    toks = [
        ["1", "He", "he", "PRON", "PRP", "_", "3", "nsubj:pass"],
        ["2", "was", "be", "AUX", "VBD", "_", "3", "aux:pass"],
        ["3", "hit", "hit", "VERB", "VBN", "Tense=Past|VerbForm=Part", "0", "root"],
        ["4", "by", "by", "ADP", "IN", "_", "6", "case"],
        ["5", "a", "a", "DET", "DT", "_", "6", "det"],
        ["6", "car", "car", "NOUN", "NN", "_", "3", "obl"],
        ["7", "and", "and", "CCONJ", "CC", "_", "9", "cc"],
        ["8", "has", "have", "AUX", "VBZ", "_", "9", "aux"],
        ["9", "left", "leave", "VERB", "VBN", "Tense=Past|VerbForm=Part", "3", "conj"],
        ["10", ".", ".", "PUNCT", ".", "_", "3", "punct"],
    ]
    toks = [c + ["_", "_"] for c in toks]
    g = gold_passive_offsets(text, toks)
    assert g == {7: True, 28: False}


def test_metrics():
    df = pd.DataFrame({"gold": [True, True, False], "pred": [True, False, False]})
    m = metrics(df)
    assert m["precision"] == 1.0 and m["recall"] == 0.5
