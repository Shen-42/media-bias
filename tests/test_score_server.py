"""Scoring function and local server for the browser extension (D-102)."""

import json
import threading
from http.client import HTTPConnection
from http.server import HTTPServer

import pytest
import spacy

from app import score_server as S
from nlp.score import score_article

TITLE = "Cyclist struck by driver in Toronto"
TEXT = (
    "A cyclist was struck on Bloor Street on Monday.\n"
    "“The car hit him hard,” a witness said.\n"
    "The city plans new lanes next year."
)


@pytest.fixture(scope="module")
def nlp():
    return spacy.load("en_core_web_sm")


def test_score_article_labels_crash_sentences_only(nlp):
    out = score_article(nlp, nlp, TITLE, TEXT)
    texts = [s["text"] for s in out]
    assert "The city plans new lanes next year." not in texts
    body = next(s for s in out if s["text"].startswith("A cyclist was struck"))
    assert body["labels"]["voice"][0] == "agentless_passive"
    assert body["suggestions"] and not body["quoted"]


def test_quoted_sentences_get_no_suggestions(nlp):
    out = score_article(nlp, nlp, TITLE, TEXT)
    quoted = [s for s in out if s["quoted"]]
    assert quoted and all(not s["suggestions"] for s in quoted)


def test_server_accepts_only_extension_origins(nlp, monkeypatch):
    monkeypatch.setattr(S, "models", lambda lang: (nlp, nlp))
    srv = HTTPServer(("127.0.0.1", 0), S.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    body = json.dumps({"title": TITLE, "text": TEXT})

    def post(origin):
        c = HTTPConnection("127.0.0.1", port)
        headers = {"Content-Type": "application/json"}
        if origin:
            headers["Origin"] = origin
        c.request("POST", "/score", body, headers)
        r = c.getresponse()
        return r.status, json.loads(r.read() or b"{}")

    assert post("https://example.com")[0] == 403
    assert post(None)[0] == 403
    status, data = post("chrome-extension://abc")
    assert status == 200 and data["sentences"]
    srv.shutdown()
