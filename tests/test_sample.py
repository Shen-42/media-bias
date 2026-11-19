import random

from eval.sample import disagreement, excluded_ids, stratified


def _cands(n=200):
    return [
        {"sentence_id": f"a{i}:b:0", "outlet": ["ctv", "global"][i % 2], "year": "2024"}
        for i in range(n)
    ]


def test_sampler_skips_excluded_ids():
    cands = _cands()
    excl = {c["sentence_id"] for c in cands[:150]} | {"a199"}  # article-level ID too
    picked = stratified(cands, 40, random.Random(0), excl)
    ids = {p["sentence_id"] for p in picked}
    assert not ids & excl
    assert "a199:b:0" not in ids
    assert len(picked) == 40


def test_disagreement_sampler_skips_excluded_ids():
    cands = [{**c, "n_disagree": 2} for c in _cands(10)]
    picked = disagreement(cands, 5, random.Random(0), {"a0:b:0", "a1:b:0"})
    assert {"a0:b:0", "a1:b:0"}.isdisjoint({p["sentence_id"] for p in picked})


def test_stratified_is_proportional():
    picked = stratified(_cands(), 40, random.Random(0), set())
    assert sum(p["outlet"] == "ctv" for p in picked) == 20


def test_excluded_file_parses(tmp_path):
    p = tmp_path / "x.txt"
    p.write_text("# comment\nabc\n\n")
    assert excluded_ids(p) == {"abc"}
