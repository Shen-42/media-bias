"""Comparison tables for the nice-to-haves (D-99 to D-101).

Crash framing rates in body sentences of initial reports, by comparison group:
  urbanist: Toronto mainstream outlets (main corpus) against Spacing, The Local and
            Canadian Cycling Magazine (data/compare.sqlite)
  cities:   Toronto (main corpus) against Vancouver and Montreal, English and French
            (data/cities.sqlite)

Text is non-quoted (newsroom plus police-matched), because no police releases were matched
outside Toronto (codebook §10). This is not the v1 newsroom rate. Wire copy is deduped
within each database. Rates carry article-cluster bootstrap 95% CIs.

    python -m analysis.compare
"""

import argparse

import pandas as pd

from analysis import measure_v15
from analysis.aggregate import TABLES, load, rates
from common import config, db

MEASURES = [
    "voice_active",
    "voice_agentless_passive",
    "voice_passive_with_agent",
    "voice_intransitive",
    "voice_nominal",
    "driver_hidden",
    "driver_ref_vehicle",
    "focus_vru",
    "vru_as_actor",
    "accident_term",
]


def comparable(sents: pd.DataFrame) -> pd.DataFrame:
    """Body crash sentences of initial reports whose headline describes a crash, outside
    quotes, canonical wire copy only. The headline rule keeps opinion and policy pieces that
    mention a crash out of both groups (D-99)."""
    crash_headline = set(sents.loc[sents.part == "headline", "article_id"])
    sents = sents[sents.article_id.isin(crash_headline)]
    s = sents[
        (sents.part == "body") & (sents.article_type == "initial") & (sents.text_source != "quoted")
    ]
    return s[s.is_canonical.isna() | (s.is_canonical == 1)]


def frame(db_path: str | None, group_of) -> pd.DataFrame:
    _, sents = load(db.connect(db_path))
    s = comparable(sents).copy()
    s["group"] = s.outlet.map(group_of)
    return s.dropna(subset=["group"])


STANCE = [
    "stance_infrastructure_any",
    "stance_infrastructure_support",
    "stance_infrastructure_oppose",
    "stance_infrastructure_outlet_held",
    "frame_legality",
    "frame_political",
    "frame_safety",
    "frame_quality_of_life",
]


def show(name: str, t: pd.DataFrame) -> None:
    cells = [
        f"{100 * r:.0f} ({100 * lo:.0f}-{100 * hi:.0f})"
        for r, lo, hi in zip(t.rate, t.ci_lo, t.ci_hi, strict=True)
    ]
    print(name)
    print(t.assign(s=cells).pivot(index="measure", columns="group", values="s").to_string())
    print(t.groupby("group")[["n_units", "n_articles"]].max().to_string())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--main", default=None)
    ap.add_argument("--urbanist", default="data/compare.sqlite")
    ap.add_argument("--cities", default="data/cities.sqlite")
    ap.add_argument("--part", choices=["urbanist", "cities", "all"], default="all")
    args = ap.parse_args()
    outlets = config.load()["outlets"]
    toronto = frame(args.main, lambda o: "toronto_mainstream")

    if args.part in ("urbanist", "all"):
        urb = frame(
            args.urbanist, lambda o: o if outlets.get(o, {}).get("group") == "urbanist" else None
        )
        t1 = rates(pd.concat([toronto, urb, urb.assign(group="urbanist_all")]), ["group"], MEASURES)
        t1.to_csv(TABLES / "compare_urbanist.csv", index=False)
        show("urbanist crash framing", t1)
        # bike-lane positions: annotated samples (D-85 Toronto census, D-99 urbanist outlets)
        tor = measure_v15.load(db.connect(args.main))
        tor = tor[tor.census].assign(group="toronto_mainstream")
        u = measure_v15.load(db.connect(args.urbanist), "measure_urbanist.csv")
        u = u.assign(group=u.outlet)
        both = pd.concat([tor, u, u.assign(group="urbanist_all")])
        both = both.dropna(subset=["stance_infrastructure_any"])
        t3 = pd.concat(
            [
                rates(both, ["group"], STANCE).assign(text_source="all"),
                rates(both, ["group", "text_source"], STANCE),
            ]
        )
        t3.to_csv(TABLES / "compare_urbanist_stance.csv", index=False)
        show("urbanist bike-lane positions", t3[t3.text_source == "all"])

    if args.part in ("cities", "all"):

        def city(o):
            c = outlets.get(o, {})
            if c.get("group") != "city":
                return None
            return f"{c.get('city')}_{c.get('language', 'en')}"

        cities = frame(args.cities, city)
        t2 = rates(pd.concat([toronto.assign(group="toronto_en"), cities]), ["group"], MEASURES)
        t2.to_csv(TABLES / "compare_cities.csv", index=False)
        show("cities crash framing", t2)


if __name__ == "__main__":
    main()
