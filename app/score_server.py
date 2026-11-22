"""Local scoring server for the browser extension (D-102). Listens on 127.0.0.1 only.

    python -m app.score_server            # then load extension/ as an unpacked extension

POST /score  {"title": ..., "text": ..., "lang": "en" | "fr"}  -> {"sentences": [...]}
GET  /health -> {"ok": true}

The page text is scored in memory and never written to disk. Requests are accepted only
from browser-extension origins.
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from nlp.score import score_article
from nlp.sentences import load_models

MAX_CHARS = 200_000
MODELS: dict[str, tuple] = {}


def models(lang: str):
    if lang not in MODELS:
        MODELS.clear()  # one language's models in memory at a time
        MODELS[lang] = load_models(lang)
    return MODELS[lang]


def allowed_origin(origin: str | None) -> bool:
    return bool(origin) and origin.startswith(("chrome-extension://", "moz-extension://"))


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        origin = self.headers.get("Origin")
        if allowed_origin(origin):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:  # CORS preflight
        self._send(204 if allowed_origin(self.headers.get("Origin")) else 403, {})

    def do_GET(self) -> None:
        self._send(200, {"ok": True}) if self.path == "/health" else self._send(404, {})

    def do_POST(self) -> None:
        if self.path != "/score":
            return self._send(404, {})
        if not allowed_origin(self.headers.get("Origin")):
            return self._send(403, {"error": "extension origins only"})
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_CHARS * 4:
            return self._send(413, {"error": "page too long"})
        try:
            req = json.loads(self.rfile.read(n))
            lang = "fr" if req.get("lang") == "fr" else "en"
            sm, trf = models(lang)
            out = score_article(
                sm, trf, str(req.get("title", ""))[:500], str(req.get("text", ""))[:MAX_CHARS], lang
            )
        except (ValueError, KeyError) as e:
            return self._send(400, {"error": str(e)})
        self._send(200, {"sentences": out})

    def log_message(self, *args) -> None:  # no page content in logs
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    models("en")
    print(f"scoring server on http://127.0.0.1:{args.port}", flush=True)
    # single-threaded: the spaCy transformer models are not shared across threads
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
