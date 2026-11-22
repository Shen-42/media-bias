"""Dashboard. Run: streamlit run app/streamlit_app.py  (MEDIA_BIAS_MODE=local for the viewer).

public mode: aggregate rates with 95% CIs and at most one flagged sentence per article
             (analysis/tables/excerpts.csv). This is the only mode that may be deployed.
local mode:  adds the full-text article viewer, read from data/ (never deployed; copyright).
"""

import os
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
TABLES = ROOT / "analysis" / "tables"
MODE = os.environ.get("MEDIA_BIAS_MODE", "public")

LABELS = {
    "driver_hidden": "Driver hidden (no person in the impact clause)",
    "voice_agentless_passive": "Agentless passive",
    "voice_passive_with_agent": "Passive with agent",
    "voice_active": "Active",
    "voice_intransitive": "Intransitive",
    "voice_nominal": "Nominal (no impact verb)",
    "driver_ref_person": "Driver referred to as a person",
    "driver_ref_vehicle": "Vehicle stands in for the driver",
    "driver_ref_absent": "No driver or vehicle",
    "focus_vru": "Pedestrian/cyclist is the subject",
    "vru_as_actor": "Pedestrian/cyclist presented as actor",
    "accident_term": "Uses 'accident'",
    "driver_ever_mentioned": "Article ever mentions a driver",
    "driver_ever_mentioned_with_quotes": "…including quotes",
    "thematic_frame": "Thematic frame (trends, design, policy)",
    "vru_conduct_any": "Mentions pedestrian/cyclist conduct",
    "driver_exceptional": "Driver exceptional (fled, impaired, criminal charge)",
    "frame_economic": "Economic frame",
    "frame_safety": "Safety frame",
    "frame_quality_of_life": "Quality-of-life frame",
    "frame_political": "Political frame",
    "frame_legality": "Legal frame",
    "stance_infrastructure_support": "Supports bike lanes",
    "stance_infrastructure_oppose": "Opposes bike lanes",
    "stance_cyclists_positive": "Positive about cyclists",
    "stance_cyclists_negative": "Negative about cyclists",
    "stance_transit_support": "Supports transit project",
    "stance_transit_oppose": "Opposes transit project",
    "loaded_language": "Loaded-language score (BABE model, mean)",
}
V15_FRAMES = [
    "frame_economic",
    "frame_safety",
    "frame_quality_of_life",
    "frame_political",
    "frame_legality",
]


def table(name: str) -> pd.DataFrame:
    p = TABLES / f"{name}.csv"
    try:
        return pd.read_csv(p)
    except (FileNotFoundError, pd.errors.EmptyDataError):  # missing or empty table
        return pd.DataFrame()


def ci_chart(df: pd.DataFrame, group: str, measures: list[str]) -> alt.Chart:
    d = df[df["measure"].isin(measures)].copy()
    d["measure"] = d["measure"].map(LABELS).fillna(d["measure"])
    d[group] = d[group].astype(str)
    base = alt.Chart(d).encode(
        y=alt.Y(f"{group}:N", title=None), color=alt.Color(f"{group}:N", legend=None)
    )
    points = base.mark_point(filled=True, size=70).encode(
        x=alt.X("rate:Q", title="Rate (95% CI)", scale=alt.Scale(domain=[0, 1])),
        tooltip=[
            group,
            "measure",
            alt.Tooltip("rate:Q", format=".2f"),
            alt.Tooltip("ci_lo:Q", format=".2f"),
            alt.Tooltip("ci_hi:Q", format=".2f"),
            "n_units",
            "n_articles",
        ],
    )
    bars = base.mark_rule().encode(x="ci_lo:Q", x2="ci_hi:Q")
    return (bars + points).properties(height=90).facet(row=alt.Row("measure:N", title=None))


def breakdown(name: str) -> None:
    """Per-outlet breakdown and outlet shares for a pooled table (D-48)."""
    shares = table("pooled_sample_shares")
    if not shares.empty:
        s = shares[shares["table"] == name]
        if not s.empty:
            top = s.loc[s["share_units"].idxmax()]
            st.caption(
                f"Pooled across outlets. Largest contributor: {top['outlet']} "
                f"({top['share_units']:.0%} of the sample)."
            )
    with st.expander("Per-outlet breakdown of this pooled sample"):
        st.dataframe(table(f"{name}_by_outlet"), use_container_width=True)
        st.dataframe(shares[shares["table"] == name] if not shares.empty else shares)


st.set_page_config(page_title="Toronto crash framing", layout="wide")
st.title("How Toronto news frames crashes involving pedestrians and cyclists")
st.caption(
    "Sentence-level framing labels from dependency rules and a weakly supervised classifier. "
    "Rates come with 95% bootstrap intervals over articles. Outlets are not ranked: where "
    "intervals overlap, no difference is claimed. Test labels came from an LLM annotator "
    "(Claude Code subagent), not a human; see the write-up for what that limits."
)

tabs = [
    "Overview",
    "Outlets",
    "Over time",
    "Police releases",
    "Examples",
    "Method",
    "Bike lanes and transit",
]
if MODE == "local":
    tabs.append("Article viewer (local only)")
tab = st.tabs(tabs)

with tab[0]:
    st.subheader("Reporter text vs. police-matched text vs. quotes")
    d = table("overall_by_text_source")
    if not d.empty:
        st.altair_chart(
            ci_chart(
                d,
                "text_source",
                ["driver_hidden", "voice_agentless_passive", "driver_ref_vehicle", "accident_term"],
            )
        )
    breakdown("overall_by_text_source")
    st.subheader("Headlines vs. body (reporter text)")
    d = table("headline_vs_body")
    if not d.empty:
        st.altair_chart(
            ci_chart(
                d,
                "part",
                ["driver_hidden", "voice_agentless_passive", "voice_nominal", "focus_vru"],
            )
        )
    breakdown("headline_vs_body")
    st.subheader("Is the driver ever mentioned? Split by exceptional driver behaviour")
    d = table("driver_mentioned_by_exceptional")
    if not d.empty:
        st.altair_chart(
            ci_chart(
                d, "exceptional", ["driver_ever_mentioned", "driver_ever_mentioned_with_quotes"]
            )
        )
    breakdown("driver_mentioned_by_exceptional")

with tab[1]:
    w = table("comparison_window")
    span = f" ({w.iloc[0]['start']} to {w.iloc[0]['end']})" if not w.empty else ""
    st.write(
        "Body sentences of initial reports, reporter text only (quotes excluded), restricted "
        f"to the window all outlets cover{span}."
    )
    wire = st.radio("Wire copy", ["Without wire stories", "With wire stories each outlet ran"])
    d = table("outlet_without_wire" if wire.startswith("Without") else "outlet_with_wire")
    if not d.empty:
        st.altair_chart(
            ci_chart(
                d,
                "outlet",
                ["driver_hidden", "voice_agentless_passive", "driver_ref_vehicle", "accident_term"],
            )
        )
    d = table("articles_by_outlet")
    if not d.empty:
        st.altair_chart(
            ci_chart(d, "outlet", ["driver_ever_mentioned", "thematic_frame", "vru_conduct_any"])
        )

with tab[2]:
    st.write(
        "Trends are shown within each outlet and never pooled: outlets cover different "
        "periods (CTV from 2025)."
    )
    d = table("year_by_outlet")
    if not d.empty:
        d = d.assign(outlet_year=d["outlet"] + " " + d["year"].astype(str))
        st.altair_chart(
            ci_chart(
                d, "outlet_year", ["driver_hidden", "voice_agentless_passive", "accident_term"]
            )
        )
    st.subheader("Before and after Bill 212 (outlets with data on both sides only)")
    d = table("bill212_pre_post_by_outlet")
    if not d.empty:
        d = d.assign(outlet_period=d["outlet"] + " " + d["period"])
        st.altair_chart(ci_chart(d, "outlet_period", ["driver_hidden", "voice_agentless_passive"]))
    st.subheader("Coverage: in-scope articles per outlet per quarter")
    st.dataframe(table("coverage_by_quarter"), use_container_width=True)
    st.dataframe(table("corpus_stats"), use_container_width=True)

with tab[3]:
    st.write(
        "Secondary analysis on the subset of articles linked to an archived Toronto Police "
        "release (Wayback Machine). About 42% of releases in the window are archived, so this "
        "subset may not represent all coverage; the bias check compares linked and unlinked "
        "articles."
    )
    st.dataframe(table("matched_vs_unmatched"), use_container_width=True)
    st.dataframe(table("police_overlap_by_outlet"), use_container_width=True)

with tab[4]:
    st.write("At most one flagged sentence per article, with the rule that fired.")
    st.dataframe(table("excerpts"), use_container_width=True)

with tab[5]:
    st.markdown(
        (ROOT / "docs" / "method.md").read_text() if (ROOT / "docs" / "method.md").exists() else ""
    )
    st.subheader("Evaluation (test set, random rows)")
    p = ROOT / "eval" / "reports" / "metrics_summary.csv"
    if p.exists():
        m = pd.read_csv(p)
        st.dataframe(m[m["sample"] == "random"], use_container_width=True)
    st.info(
        "Suggestions from the Road Collision Reporting Guidelines are suggestions, not "
        "measured results: name the driver as a person, prefer 'crash' or 'collision' to "
        "'accident', and say who struck whom."
    )

with tab[6]:
    st.warning(
        "Exploratory. Stance shares come from the Snorkel label model on a random sample of "
        "sentences that name a target (D-84). Its stance precision is about 0.4-0.6, so the "
        "levels run about twice the annotated rates (transit: 18% vs 9%); compare text "
        "sources, not levels. Frame shares come from SetFit, which failed validation (D-80), "
        "and are for diagnosis only. Quoted, attributed and the outlet's own text are kept "
        "apart: an attributed stance is the source's, not the outlet's. See the write-up."
    )
    topic = st.radio("Topic", ["bike_lane", "transit"], horizontal=True)
    d = table("v15_frames_by_source")
    if not d.empty:
        st.subheader("Policy frames by text source")
        st.altair_chart(ci_chart(d[d["topic"] == topic], "text_source", V15_FRAMES))
    d = table("v15_stance_by_source")
    if not d.empty:
        st.subheader("Stance by text source")
        stance = [m for m in d["measure"].unique() if m in LABELS]
        st.altair_chart(ci_chart(d[d["topic"] == topic], "text_source", stance))
    d = table("v15_frames_by_outlet")
    if not d.empty:
        st.subheader("Reporter text by outlet")
        d = d[(d["topic"] == topic) & (d["text_source"] == "newsroom")]
        st.altair_chart(ci_chart(d, "outlet", V15_FRAMES))
    if topic == "bike_lane":
        d = table("v15_bike_lane_by_period")
        if not d.empty:
            st.subheader("Bill 212 periods (reporter text)")
            d = d[d["text_source"] == "newsroom"]
            st.altair_chart(
                ci_chart(
                    d,
                    "period",
                    [
                        "frame_legality",
                        "frame_safety",
                        "stance_infrastructure_support",
                        "stance_infrastructure_oppose",
                    ],
                )
            )
            st.dataframe(pd.read_csv(ROOT / "analysis" / "timeline_bill212.csv"), hide_index=True)
    st.subheader("Who is quoted")
    d = table("v15_source_roles")
    if not d.empty:
        st.dataframe(d[d["topic"] == topic], use_container_width=True, hide_index=True)
    d = table("v15_stance_by_role")
    if not d.empty:
        st.caption("Stance of quoted sentences by the speaker's role (the speaker's view).")
        st.dataframe(d[d["topic"] == topic], use_container_width=True, hide_index=True)

if MODE == "local":
    with tab[-1]:
        from common import db

        con = db.connect()
        arts = pd.read_sql(
            "SELECT id, outlet, published, title FROM articles WHERE is_crash=1 AND is_toronto=1"
            " ORDER BY published DESC",
            con,
        )
        pick = st.selectbox(
            "Article",
            arts["id"],
            format_func=lambda i: " | ".join(
                arts.loc[arts["id"] == i, ["published", "outlet", "title"]].iloc[0].astype(str)
            ),
        )
        sents = pd.read_sql(
            "SELECT id, part, text, is_crash, text_source, release_sim FROM sentences"
            " WHERE article_id=? ORDER BY part DESC, idx",
            con,
            params=(pick,),
        )
        labs = pd.read_sql(
            "SELECT sentence_id, label, value, evidence FROM labels WHERE source IN"
            " ('rule','setfit') AND sentence_id LIKE ?",
            con,
            params=(f"{pick}:%",),
        )
        for _, s in sents.iterrows():
            own = labs[labs["sentence_id"] == s["id"]]
            flagged = s["is_crash"] or (own["value"] == "true").any()
            st.markdown(("**" if flagged else "") + s["text"] + ("**" if flagged else ""))
            if flagged:
                st.caption(f"text_source={s['text_source']} release_sim={s['release_sim']}")
                st.dataframe(own[["label", "value", "evidence"]], hide_index=True)
