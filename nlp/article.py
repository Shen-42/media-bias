"""Article-level labels (codebook §4): driver mention, exceptional driver, thematic frame,
VRU conduct, police overlap. Fuzzy rollups use the SetFit end model's sentence labels.
"""

import argparse

from common import db
from nlp import lexicons as lx


def exceptional(text: str) -> tuple[bool, str]:
    for name, rx in (
        ("fled", lx.FLED_RE),
        ("impaired", lx.IMPAIRED_RE),
        ("criminal charge", lx.CRIMINAL_CHARGE_RE),
    ):
        if m := rx.search(text):
            return True, f"{name}: '{m.group(0)}'"
    return False, ""


def overlap_share(rows: list[dict]) -> float | None:
    """D-14: police_matched share of non-quoted body sentences; None without a release."""
    body = [r for r in rows if r["part"] == "body" and r["text_source"] != "quoted"]
    if not body or all(r["release_sim"] is None for r in body):
        return None
    return sum(r["text_source"] == "police_matched" for r in body) / len(body)


def article_labels(art: dict, rows: list[dict], sent_labels: dict) -> dict[str, tuple]:
    def lab(sid, name, source):
        return sent_labels.get((sid, name, source))

    drv = [r for r in rows if lab(r["id"], "driver_mention", "rule") == "true"]
    primary = [r for r in drv if r["text_source"] != "quoted"]
    exc, exc_ev = exceptional(f"{art['title'] or ''}\n{art['text'] or ''}")
    hta = lx.HTA_CHARGE_RE.search(art["text"] or "")
    them = [
        r for r in rows if r["part"] == "body" and lab(r["id"], "thematic_cue", "setfit") == "true"
    ]
    cond = [
        r
        for r in rows
        if r["part"] == "body"
        and r["is_vru"]
        and lab(r["id"], "vru_conduct_detail", "setfit") == "true"
    ]
    ov = overlap_share(rows)
    return {
        "driver_ever_mentioned": (bool(primary), primary[0]["id"] if primary else ""),
        "driver_ever_mentioned_with_quotes": (bool(drv), drv[0]["id"] if drv else ""),
        "driver_exceptional": (exc, exc_ev),
        "driver_hta_charge": (bool(hta), hta.group(0) if hta else ""),
        "thematic_frame": (bool(them), them[0]["id"] if them else ""),
        "vru_conduct_any": (bool(cond), cond[0]["id"] if cond else ""),
        "police_overlap": (ov, "share of non-quoted body sentences"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
    sent_labels = {
        (r["sentence_id"], r["label"], r["source"]): r["value"]
        for r in con.execute(
            "SELECT sentence_id, label, source, value FROM labels WHERE source IN ('rule','setfit')"
            " AND label IN ('driver_mention','thematic_cue','vru_conduct_detail')"
        )
    }
    arts = con.execute("SELECT * FROM articles WHERE is_crash=1 AND is_toronto=1").fetchall()
    for a in arts:
        rows = [
            dict(r) for r in con.execute("SELECT * FROM sentences WHERE article_id=?", (a["id"],))
        ]
        for name, (value, ev) in article_labels(dict(a), rows, sent_labels).items():
            v = (
                None
                if value is None
                else (str(value).lower() if isinstance(value, bool) else value)
            )
            con.execute(
                "INSERT OR REPLACE INTO article_labels VALUES (?,?,?,?,?)",
                (a["id"], name, "pipeline", v, ev),
            )
    con.commit()
    print(f"article labels: {len(arts)} articles", flush=True)


if __name__ == "__main__":
    main()
