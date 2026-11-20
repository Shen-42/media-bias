import random

from eval.sample import disagreement, excluded_ids, stratified, topup


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


def test_topup_drops_out_of_scope_and_refills_random():
    cands = {"crash": _cands(50), "context": [], "text_source": []}
    in_scope = {c["sentence_id"] for c in cands["crash"]}
    rows = [
        {"sentence_id": "a0:b:0", "set": "crash", "sample": "random", "voice": "active"},
        {"sentence_id": "gone:b:0", "set": "crash", "sample": "random", "voice": "nominal"},
        {"sentence_id": "a1:b:0", "set": "crash", "sample": "random", "voice": ""},
    ]
    excl = {"a2:b:0"}
    kept, new = topup(rows, cands, {"crash": 4}, random.Random(0), excl, taken={"a3:b:0"})
    assert [r["sentence_id"] for r in kept] == ["a0:b:0", "a1:b:0"]
    assert kept[0]["voice"] == "active"  # labels survive
    assert len(new) == 2
    new_ids = {r["sentence_id"] for r in new}
    assert new_ids <= in_scope
    assert new_ids.isdisjoint({"a0:b:0", "a1:b:0", "a2:b:0", "a3:b:0"})
    assert all(r["sample"] == "random" and r["set"] == "crash" for r in new)
