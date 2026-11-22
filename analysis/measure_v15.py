"""v1.5 stance rates from the annotated measurement sample (D-85).

Bike infrastructure and cyclists: census of body sentences naming the target, so rates cover
every such sentence. Transit: 200 random transit-mention body sentences per outlet; the
all-outlet rate weights each outlet by its share of transit-mention sentences.
Intervals are article-cluster bootstrap 95% CIs (resampled within outlet for transit).
Every table is split by text_source (quoted, attributed, newsroom); they are never pooled.
"""

import argparse

import numpy as np
import pandas as pd

from analysis.aggregate import N_BOOT, TABLES, rates
from analysis.aggregate_v15 import period_of, periods, text_source
from common import db
from eval.sample import EVAL, read_csv
from nlp import v15

STANCE = {
    "stance_infrastructure": ("support", "oppose"),
    "stance_cyclists": ("positive", "negative"),
    "stance_transit": ("support", "oppose"),
}


def load(con) -> pd.DataFrame:
    gold = {r["sentence_id"]: r for r in read_csv(EVAL / "measure_v15.csv")}
    art = {r["id"]: r for r in con.execute("SELECT id, outlet, published FROM articles")}
    stored = {r[0]: r[1] for r in con.execute("SELECT id, text_source FROM sentences")}
    ps = periods()
    rows = []
    for s in v15.v15_sentences(con):
        g = gold.get(s["id"])
        if g is None or not g["stance_transit"]:
            continue
        a = art[s["article_id"]]
        r = {
            "sentence_id": s["id"],
            "article_id": s["article_id"],
            "outlet": a["outlet"],
            "period": period_of(a["published"] or "", ps),
            "text_source": text_source(s, stored.get(s["id"])),
            "census": "census" in g["sample"],
            "transit_random": "transit_random" in g["sample"],
        }
        for label, (pos, neg) in STANCE.items():
            has = bool(v15.TARGETS[label].search(s["text"]))
            r[f"{label}_{pos}"] = float(g[label] == pos) if has else None
            r[f"{label}_{neg}"] = float(g[label] == neg) if has else None
            r[f"{label}_any"] = float(g[label] in (pos, neg)) if has else None
            # the outlet's own position (codebook 9.2 stance_holder, D-87)
            own = g[label] in (pos, neg) and g.get("stance_holder") == "outlet"
            r[f"{label}_outlet_held"] = float(own) if has else None
        rows.append(r)
    return pd.DataFrame(rows)


def cols(label: str) -> list[str]:
    pos, neg = STANCE[label]
    return [f"{label}_any", f"{label}_{pos}", f"{label}_{neg}"]


def stratified_rate(df: pd.DataFrame, value: str, weights: dict[str, float], seed: int = 0):
    """Outlet-weighted mean of a 0/1 column; bootstrap resamples articles within each outlet."""
    df = df.dropna(subset=[value])
    parts = []
    for outlet, sub in df.groupby("outlet"):
        g = sub.groupby("article_id")[value].agg(["sum", "count"])
        parts.append((weights[outlet], g["sum"].to_numpy(float), g["count"].to_numpy(float)))
    if not parts:
        return np.nan, np.nan, np.nan, 0
    total = sum(w for w, _, _ in parts)
    est = sum(w * s.sum() / c.sum() for w, s, c in parts) / total
    rng = np.random.default_rng(seed)
    boots = np.zeros(N_BOOT)
    for w, s, c in parts:
        idx = rng.integers(0, len(s), (N_BOOT, len(s)))
        boots += w * s[idx].sum(1) / np.maximum(c[idx].sum(1), 1)
    lo, hi = np.percentile(boots / total, [2.5, 97.5])
    return est, lo, hi, int(len(df))


def transit_weights(con) -> dict[str, float]:
    """Share of transit-mention body sentences per outlet (the draw's strata)."""
    art = {r[0]: r[1] for r in con.execute("SELECT id, outlet FROM articles")}
    rx = v15.TARGETS["stance_transit"]
    s = pd.Series(
        [
            art[x["article_id"]]
            for x in v15.v15_sentences(con)
            if x["part"] == "body" and rx.search(x["text"])
        ]
    )
    return s.value_counts(normalize=True).to_dict()


def build(df: pd.DataFrame, weights: dict[str, float]) -> dict[str, pd.DataFrame]:
    census = df[df.census]
    infra, cyc = cols("stance_infrastructure"), cols("stance_cyclists")
    out = {
        "v15m_infra_by_source": rates(census, ["text_source"], infra),
        "v15m_infra_by_outlet": rates(census, ["text_source", "outlet"], infra),
        "v15m_infra_by_period": rates(census, ["text_source", "period"], infra),
        "v15m_cyclists_by_source": rates(census, ["text_source"], cyc),
    }
    tr = df[df.transit_random]
    tcols = cols("stance_transit")
    out["v15m_transit_by_outlet"] = rates(tr, ["text_source", "outlet"], tcols)
    rows = []
    for src, sub in tr.groupby("text_source"):
        for v in tcols:
            est, lo, hi, n = stratified_rate(sub, v, weights)
            rows.append(
                {
                    "text_source": src,
                    "measure": v,
                    "rate": est,
                    "ci_lo": lo,
                    "ci_hi": hi,
                    "n_units": n,
                    "n_articles": sub.dropna(subset=[v]).article_id.nunique(),
                }
            )
    out["v15m_transit_by_source"] = pd.DataFrame(rows)
    # Outlet-held stance (D-87): not split by text_source, since it already says whose voice.
    out["v15m_outlet_held"] = pd.concat(
        [
            rates(census, ["outlet"], ["stance_infrastructure_outlet_held"]),
            rates(tr, ["outlet"], ["stance_transit_outlet_held"]),
        ]
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
    df = load(con)
    TABLES.mkdir(parents=True, exist_ok=True)
    for name, t in build(df, transit_weights(con)).items():
        t.to_csv(TABLES / f"{name}.csv", index=False)
    print(f"v15 measure: {len(df)} annotated sentences -> {TABLES}")


if __name__ == "__main__":
    main()
