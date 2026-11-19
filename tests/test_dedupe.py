from collect.dedupe import groups

BODY = (
    "Toronto police say a cyclist was struck by a driver at Bloor Street West and Spadina "
    "Avenue on Tuesday morning. The cyclist was taken to hospital with serious injuries. "
    "The driver remained at the scene. Police are asking anyone with dashcam footage to "
    "contact investigators. Roads in the area were closed for several hours."
)


def test_wire_copy_grouped_with_earliest_canonical():
    docs = [
        ("b", "2024-05-02", BODY + " The Canadian Press."),
        ("a", "2024-05-01", BODY),
        ("c", "2024-05-01", "A completely different story about a pedestrian on Finch Avenue " * 5),
    ]
    g = groups(docs)
    assert g["a"] == "a" and g["b"] == "a"
    assert "c" not in g
