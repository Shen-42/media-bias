"""Qwen via local Ollama as one labeling function (CLAUDE.md rules for every Qwen call).

Non-thinking mode, temperature 0, fixed seed, JSON constrained by a schema that lists only
codebook labels. Invalid output is an abstain. Responses are cached by
(model digest, prompt hash, sentence id). Sentences are sent in small batches (D-36).
"""

import argparse
import hashlib
import json
from pathlib import Path

from common import config, db

PROMPTS = Path(__file__).parent / "prompts"
TASKS = {
    "crash": {
        "prompt": "crash_v1.txt",
        "fields": {
            "voice": [
                "active",
                "passive_with_agent",
                "agentless_passive",
                "intransitive",
                "nominal",
            ],
            "driver_reference": ["person", "vehicle", "absent"],
            "focus": ["vru", "driver", "vehicle", "other"],
            "vru_as_actor": [True, False],
            "accident_term": [True, False],
        },
    },
    "context": {
        "prompt": "context_v1.txt",
        "fields": {"vru_conduct_detail": [True, False], "thematic_cue": [True, False]},
    },
    "v15": {
        "prompt": "v15_v2.txt",
        "fields": {
            "policy_frame": [
                "economic",
                "safety",
                "quality_of_life",
                "political",
                "legality",
                "other",
                "none",
            ],
            "stance_infrastructure": ["support", "oppose", "none"],
            "stance_cyclists": ["positive", "negative", "none"],
            "stance_transit": ["support", "oppose", "none"],
        },
    },
}
BATCH = 8
CACHE = """CREATE TABLE IF NOT EXISTS qwen_cache (
    digest TEXT, prompt_hash TEXT, sentence_id TEXT, response TEXT,
    PRIMARY KEY (digest, prompt_hash, sentence_id))"""


def schema(task: str) -> dict:
    props = {"id": {"type": "string"}}
    for name, values in TASKS[task]["fields"].items():
        if values == [True, False]:
            props[name] = {"type": "boolean"}
        else:
            props[name] = {"type": "string", "enum": values}
    item = {"type": "object", "properties": props, "required": list(props)}
    return {
        "type": "object",
        "properties": {"items": {"type": "array", "items": item}},
        "required": ["items"],
    }


def validate(task: str, item: dict) -> dict:
    """Keep only valid codebook values; anything else is an abstain (None)."""
    out = {}
    for name, values in TASKS[task]["fields"].items():
        v = item.get(name)
        out[name] = str(v).lower() if v in values else None
    return out


def prompt_hash(task: str) -> str:
    text = (PROMPTS / TASKS[task]["prompt"]).read_text()
    return hashlib.sha256((text + json.dumps(schema(task), sort_keys=True)).encode()).hexdigest()[
        :16
    ]


class Qwen:
    def __init__(self, con):
        import ollama

        cfg = config.load()["qwen"]
        self.cfg = cfg
        self.client = ollama.Client(host=cfg["host"])
        self.digest = _digest(self.client, cfg["tag"])
        if cfg["digest"] and cfg["digest"] != self.digest:
            raise RuntimeError(f"{cfg['tag']} digest {self.digest} != pinned {cfg['digest']}")
        self.con = con
        con.execute(CACHE)

    def _call(self, task: str, batch: list[tuple[str, str]]) -> dict[str, dict]:
        system = (PROMPTS / TASKS[task]["prompt"]).read_text()
        lines = "\n".join(f'{{"id": "{i}", "sentence": {json.dumps(t)}}}' for i, t in batch)
        r = self.client.chat(
            model=self.cfg["tag"],
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Label these sentences:\n{lines}"},
            ],
            format=schema(task),
            think=False,
            options={
                "temperature": self.cfg["temperature"],
                "seed": self.cfg["seed"],
                "num_ctx": self.cfg["num_ctx"],
            },
        )
        try:
            items = json.loads(r.message.content)["items"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return {}
        return {str(it.get("id")): it for it in items if isinstance(it, dict)}

    def label(self, task: str, rows: list[tuple[str, str]]) -> dict[str, dict]:
        ph = prompt_hash(task)
        out, todo = {}, []
        for sid, text in rows:
            hit = self.con.execute(
                "SELECT response FROM qwen_cache"
                " WHERE digest=? AND prompt_hash=? AND sentence_id=?",
                (self.digest, ph, sid),
            ).fetchone()
            if hit:
                out[sid] = json.loads(hit[0])
            else:
                todo.append((sid, text))
        for i in range(0, len(todo), BATCH):
            batch = todo[i : i + BATCH]
            local = [(str(k), t) for k, (_, t) in enumerate(batch)]
            got = self._call(task, local)
            for k, (sid, _) in enumerate(batch):
                rec = validate(task, got.get(str(k), {}))
                out[sid] = rec
                self.con.execute(
                    "INSERT OR REPLACE INTO qwen_cache VALUES (?,?,?,?)",
                    (self.digest, ph, sid, json.dumps(rec)),
                )
            self.con.commit()
            if (i // BATCH) % 25 == 0:
                print(f"qwen {task} {i}/{len(todo)}", flush=True)
        return out


def _digest(client, tag: str) -> str:
    for m in client.list().models:
        if m.model == tag:
            return m.digest
    raise RuntimeError(f"{tag} not pulled")


def run(con, task: str, rows: list[tuple[str, str]]) -> None:
    q = Qwen(con)
    for sid, rec in q.label(task, rows).items():
        for name, value in rec.items():
            con.execute(
                "INSERT OR REPLACE INTO labels VALUES (?,?,?,?,?,?)",
                (sid, name, "qwen", value, None, f"qwen {q.cfg['tag']} {TASKS[task]['prompt']}"),
            )
    con.commit()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("task", choices=TASKS)
    ap.add_argument("ids", help="file with sentence ids")
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
    ids = {ln.strip() for ln in open(args.ids) if ln.strip()}
    rows = [
        (r["id"], r["text"])
        for r in con.execute("SELECT id, text FROM sentences")
        if r["id"] in ids
    ]
    run(con, args.task, rows)


if __name__ == "__main__":
    main()
