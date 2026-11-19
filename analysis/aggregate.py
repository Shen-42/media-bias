"""Aggregate framing rates with bootstrap CIs over articles (PLAN.md §10, §11 Phase 3).

Outputs only aggregates (analysis/tables/*.csv), which may be published. Primary analysis:
initial reports, canonical copies, newsroom + police-matched text kept separate from quotes.
"""

import argparse
import json

import numpy as np
import pandas as pd

from common import config, db

TABLES = config.ROOT / "analysis" / "tables"
N_BOOT = 1000


def rate_ci(df: pd.DataFrame, value: str, cluster: str = "article_id", seed: int = 0):
    """Mean of a 0/1 column with a cluster (article) bootstrap 95% CI."""
    if df.empty:
        return np.nan, np.nan, np.nan, 0, 0
    g = df.groupby(cluster)[value].agg(["sum", "count"])
    s, c = g["sum"].to_numpy(float), g["count"].to_numpy(float)
    est = s.sum() / c.sum()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(g), (N_BOOT, len(g)))
    boots = s[idx].sum(1) / np.maximum(c[idx].sum(1), 1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return est, lo, hi, int(c.sum()), len(g)


def rates(df: pd.DataFrame, by: list[str], values: list[str]) -> pd.DataFrame:
    out = []
    groups = df.groupby(by) if by else [((), df)]
    for key, sub in groups:
        key = key if isinstance(key, tuple) else (key,)
        for v in values:
            est, lo, hi, n, n_art = rate_ci(sub.dropna(subset=[v]), v)
            out.append(
                {
                    **dict(zip(by, key, strict=True)),
                    "measure": v,
                    "rate": est,
                    "ci_lo": lo,
                    "ci_hi": hi,
                    "n_units": n,
                    "n_articles": n_art,
                }
            )
    return pd.DataFrame(out)


def load(con) -> tuple[pd.DataFrame, pd.DataFrame]:
    arts = pd.read_sql(
        "SELECT id AS article_id, outlet, published, severity, road_users, article_type,"
        " is_canonical, wire_group, release_id, hit_and_run FROM articles"
        " WHERE is_crash=1 AND is_toronto=1",
        con,
    )
    arts["year"] = arts["published"].str[:4]
    arts["fatal"] = arts["severity"].eq("fatal")
    arts["linked"] = arts["release_id"].notna()
    arts["wire"] = arts["wire_group"].notna()
    al = pd.read_sql("SELECT article_id, label, value FROM article_labels", con)
    al = al.pivot_table(index="article_id", columns="label", values="value", aggfunc="first")
    arts = arts.merge(al, left_on="article_id", right_index=True, how="left")
    for c in (
        "driver_ever_mentioned",
        "driver_ever_mentioned_with_quotes",
        "driver_exceptional",
        "thematic_frame",
        "vru_conduct_any",
        "driver_hta_charge",
    ):
        if c in arts:
            arts[c] = arts[c].map({"true": 1.0, "false": 0.0})
    if "police_overlap" in arts:
        arts["police_overlap"] = pd.to_numeric(arts["police_overlap"], errors="coerce")

    sents = pd.read_sql(
        "SELECT s.id, s.article_id, s.part, s.text_source, s.is_crash FROM sentences s"
        " JOIN articles a ON a.id = s.article_id WHERE a.is_crash=1 AND a.is_toronto=1"
        " AND s.is_crash=1",
        con,
    )
    lab = pd.read_sql(
        "SELECT sentence_id, label, value FROM labels WHERE source='rule' AND label IN"
        " ('voice','driver_reference','focus','vru_as_actor','accident_term')",
        con,
    ).pivot_table(index="sentence_id", columns="label", values="value", aggfunc="first")
    sents = sents.merge(lab, left_on="id", right_index=True, how="left")
    sents = sents.merge(
        arts[
            [
                "article_id",
                "outlet",
                "published",
                "year",
                "article_type",
                "is_canonical",
                "wire",
                "fatal",
                "linked",
                "hit_and_run",
            ]
        ],
        on="article_id",
    )
    for v in ("active", "passive_with_agent", "agentless_passive", "intransitive", "nominal"):
        sents[f"voice_{v}"] = (sents["voice"] == v).astype(float)
    for v in ("person", "vehicle", "absent"):
        sents[f"driver_ref_{v}"] = (sents["driver_reference"] == v).astype(float)
    sents["focus_vru"] = (sents["focus"] == "vru").astype(float)
    sents["vru_as_actor"] = (sents["vru_as_actor"] == "true").astype(float)
    sents["accident_term"] = (sents["accident_term"] == "true").astype(float)
    # Driver hidden: no person in the impact clause (vehicle metonymy or absent).
    sents["driver_hidden"] = sents["driver_reference"].isin(["vehicle", "absent"]).astype(float)
    return arts, sents


SENT_MEASURES = [
    "driver_hidden",
    "voice_agentless_passive",
    "voice_passive_with_agent",
    "voice_active",
    "voice_intransitive",
    "voice_nominal",
    "driver_ref_person",
    "driver_ref_vehicle",
    "driver_ref_absent",
    "focus_vru",
    "vru_as_actor",
    "accident_term",
]
ART_MEASURES = ["driver_ever_mentioned", "thematic_frame", "vru_conduct_any", "driver_exceptional"]


def common_window(arts: pd.DataFrame) -> tuple[str, str]:
    """Dates every outlet covers: latest first article to earliest last article (D-45)."""
    g = arts.groupby("outlet")["published"].agg(["min", "max"])
    return str(g["min"].max())[:10], str(g["max"].min())[:10]


def in_window(df: pd.DataFrame, window: tuple[str, str]) -> pd.DataFrame:
    return df[df["published"].str[:10].between(*window)]


def pre_post(df: pd.DataFrame, cutoff: str) -> pd.DataFrame:
    """Label pre/post a date; keep only outlets with data on both sides (D-45)."""
    df = df.assign(period=df["published"].str[:10].lt(cutoff).map({True: "pre", False: "post"}))
    both = df.groupby("outlet")["period"].nunique()
    return df[df["outlet"].isin(both[both == 2].index)]


def coverage_by_quarter(arts: pd.DataFrame) -> pd.DataFrame:
    q = pd.PeriodIndex(arts["published"].str[:10], freq="Q").astype(str)
    a = arts.assign(quarter=q, initial=arts["article_type"].eq("initial"))
    g = (
        a.groupby(["quarter", "outlet"])
        .agg(articles=("article_id", "count"), initial_reports=("initial", "sum"))
        .reset_index()
    )
    wide = g.pivot_table(
        index="quarter", columns="outlet", values="articles", aggfunc="sum", fill_value=0
    )
    return wide.astype(int).reset_index()


def build_tables(
    arts: pd.DataFrame, sents: pd.DataFrame, bill212: str = "2024-11-25"
) -> dict[str, pd.DataFrame]:
    window = common_window(arts)
    init = sents[sents["article_type"] == "initial"]
    canon_body = init[(init["part"] == "body") & (init["is_canonical"] == 1)]
    reporter = canon_body[canon_body["text_source"] != "quoted"]
    a_init = arts[(arts["article_type"] == "initial")]
    t = {}
    t["overall_by_text_source"] = rates(canon_body, ["text_source"], SENT_MEASURES)
    t["headline_vs_body"] = rates(
        pd.concat([init[init["part"] == "headline"], reporter]), ["part"], SENT_MEASURES
    )
    # Per outlet: includes wire stories each outlet ran; reported with and without wire (Q17).
    body_all = init[(init["part"] == "body") & (init["text_source"] != "quoted")]
    # Outlet comparisons: only the window all outlets cover (D-45).
    body_w = in_window(body_all, window)
    t["outlet_with_wire"] = rates(body_w, ["outlet"], SENT_MEASURES)
    t["outlet_without_wire"] = rates(body_w[~body_w["wire"]], ["outlet"], SENT_MEASURES)
    t["outlet_headlines"] = rates(
        in_window(init[init["part"] == "headline"], window), ["outlet"], SENT_MEASURES
    )
    # Trends: within each outlet, never pooled across outlets (D-45).
    t["year_by_outlet"] = rates(body_all, ["outlet", "year"], SENT_MEASURES)
    pp = pre_post(body_all, bill212)
    t["bill212_pre_post_by_outlet"] = (
        rates(pp, ["outlet", "period"], SENT_MEASURES) if not pp.empty else pd.DataFrame()
    )
    t["fatal_vs_nonfatal"] = rates(reporter, ["fatal"], SENT_MEASURES)
    fu = sents[
        (sents["part"] == "body")
        & (sents["is_canonical"] == 1)
        & (sents["text_source"] != "quoted")
        & sents["article_type"].isin(["initial", "follow_up"])
    ]
    t["initial_vs_follow_up"] = rates(fu, ["article_type"], SENT_MEASURES)
    a_init = a_init.assign(
        exceptional=a_init["driver_exceptional"].map({1.0: "exceptional", 0.0: "ordinary"})
    )
    t["driver_mentioned_by_exceptional"] = rates(
        a_init, ["exceptional"], ["driver_ever_mentioned", "driver_ever_mentioned_with_quotes"]
    )
    t["articles_by_outlet"] = rates(in_window(a_init, window), ["outlet"], ART_MEASURES)
    t["articles_overall"] = rates(a_init, [], ART_MEASURES)
    linked = in_window(a_init[a_init["linked"]], window)
    t["police_overlap_by_outlet"] = (
        linked.groupby("outlet")["police_overlap"].agg(["mean", "median", "count"]).reset_index()
    )
    t["matched_vs_unmatched"] = matched_bias_check(a_init, init)
    t["corpus_stats"] = corpus_stats(arts)
    t["coverage_by_quarter"] = coverage_by_quarter(arts)
    t["comparison_window"] = pd.DataFrame(
        [{"start": window[0], "end": window[1], "bill212_cutoff": bill212}]
    )
    return t


def matched_bias_check(arts: pd.DataFrame, sents: pd.DataFrame) -> pd.DataFrame:
    """Compare articles with and without an archived, linked release (PLAN.md §6 step 2)."""
    rows = []
    for linked, sub in arts.groupby("linked"):
        users = sub["road_users"].map(lambda s: json.loads(s) if s else [])
        rows.append(
            {
                "linked": linked,
                "articles": len(sub),
                "share_fatal": sub["fatal"].mean(),
                "share_cyclist": users.map(lambda u: "cyclist" in u).mean(),
                "share_hit_and_run": sub["hit_and_run"].mean(),
                **{
                    f"share_{o}": (sub["outlet"] == o).mean()
                    for o in sorted(arts["outlet"].unique())
                },
                **{f"share_{y}": (sub["year"] == y).mean() for y in sorted(arts["year"].unique())},
            }
        )
    head = sents[sents["part"] == "headline"]
    out = pd.DataFrame(rows)
    for linked in (False, True):
        h = head[head["linked"] == linked]
        out.loc[out["linked"] == linked, "headline_driver_hidden"] = (
            h["driver_hidden"].mean() if len(h) else np.nan
        )
    return out


def corpus_stats(arts: pd.DataFrame) -> pd.DataFrame:
    a = arts.assign(month=arts["published"].str[:7])
    g = (
        a.groupby(["outlet", "month"])
        .agg(articles=("article_id", "count"), linked=("linked", "sum"))
        .reset_index()
    )
    g["share_linked"] = g["linked"] / g["articles"]
    return g


def excerpts(con, n: int = 20, max_words: int = 25, seed: int = 0) -> pd.DataFrame:
    """At most one flagged sentence per article, truncated, for the public dashboard."""
    df = pd.read_sql(
        "SELECT s.id, s.article_id, s.text, a.outlet, substr(a.published,1,7) AS month,"
        " l1.value AS voice, l2.value AS driver_reference, l1.evidence AS evidence"
        " FROM sentences s JOIN articles a ON a.id = s.article_id"
        " JOIN labels l1 ON l1.sentence_id = s.id AND l1.label='voice' AND l1.source='rule'"
        " JOIN labels l2 ON l2.sentence_id = s.id AND l2.label='driver_reference'"
        " AND l2.source='rule' WHERE a.is_crash=1 AND a.is_toronto=1 AND s.part='body'"
        " AND a.article_type='initial' AND s.text_source != 'quoted'",
        con,
    )
    if df.empty:
        return df
    df = df.groupby("article_id").head(1).sample(frac=1, random_state=seed).head(n)

    def cut(t: str) -> str:
        w = t.split()
        return " ".join(w[:max_words]) + (" …" if len(w) > max_words else "")

    df["excerpt"] = df["text"].map(cut)
    return df[["outlet", "month", "excerpt", "voice", "driver_reference", "evidence"]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    args = ap.parse_args()
    con = db.connect(args.db)
    arts, sents = load(con)
    TABLES.mkdir(parents=True, exist_ok=True)
    cutoff = config.load().get("analysis", {}).get("bill212_cutoff", "2024-11-25")
    for name, df in build_tables(arts, sents, cutoff).items():
        df.to_csv(TABLES / f"{name}.csv", index=False)
    excerpts(con).to_csv(TABLES / "excerpts.csv", index=False)
    print(f"analysis: {len(arts)} articles, {len(sents)} crash sentences -> {TABLES}")


if __name__ == "__main__":
    main()
