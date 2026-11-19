from nlp.coref import sentence_flags


def _sents(body: str) -> list[dict]:
    out, pos = [], 0
    for i, part in enumerate(body.split(". ")):
        start = body.index(part, pos)
        out.append({"idx": i, "text": part, "start": start, "end": start + len(part)})
        pos = start + len(part)
    return out


def test_coref_links_description_to_driver():
    body = "A man was behind the wheel of an SUV. The driver struck a cyclist. He stayed"
    sents = _sents(body)
    man = (body.index("A man"), body.index("A man") + 5)
    drv = (body.index("The driver"), body.index("The driver") + 10)
    he = (body.index("He"), body.index("He") + 2)
    flags = sentence_flags(sents, [[man, drv, he]], body)
    assert [f["driver"] for f in flags] == [True, True, True]
    assert flags[2]["driver_ev"].startswith("coref")


def test_no_driver_cluster_no_flag():
    body = "A cyclist was struck. She was taken to hospital"
    sents = _sents(body)
    cyc = (body.index("A cyclist"), body.index("A cyclist") + 9)
    she = (body.index("She"), body.index("She") + 3)
    flags = sentence_flags(sents, [[cyc, she]], body)
    assert [f["driver"] for f in flags] == [False, False]
    assert [f["vru"] for f in flags] == [True, True]
