"""Build the project site (site/index.html) from the aggregate tables.

    python site/build.py

Every rate on the page is read from analysis/tables/ or eval/reports/, so the site
cannot drift from the published tables. Design brief: docs/site-design.md.
"""

import csv
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "analysis" / "tables"
REPO = "https://github.com/Shen-42/media-bias"


def load(name: str) -> dict:
    """Map (group, measure) -> row for tables shaped group,measure,rate,ci_lo,ci_hi,n_units,n_articles."""
    with open(TABLES / f"{name}.csv") as f:
        rows = list(csv.reader(f))
    out = {}
    for r in rows[1:]:
        out[(r[0], r[1])] = {
            "rate": float(r[2]),
            "lo": float(r[3]),
            "hi": float(r[4]),
            "n": int(r[5]),
            "articles": int(r[6]),
        }
    return out


def pct(x: float) -> str:
    v = x * 100
    if v == 0:
        return "0%"
    return f"{v:.1f}%" if v < 2 else f"{v:.0f}%"


def rc(r: dict) -> str:
    return f"{pct(r['rate'])} ({ci(r)})"


def ci(r: dict) -> str:
    if r["rate"] == 0:  # a 0-0 bootstrap interval understates uncertainty: rule of three
        return f"0–{300 / r['n']:.1f}"
    lo, hi = r["lo"] * 100, r["hi"] * 100
    fmt = (lambda v: f"{v:.1f}") if hi < 2 else (lambda v: f"{v:.0f}")
    return f"{fmt(lo)}–{fmt(hi)}"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def code(s: str) -> str:
    return f"<code>{esc(s)}</code>"


def link(path: str, text: str | None = None) -> str:
    return f'<a href="{REPO}/blob/main/{path}">{text or code(path)}</a>'


# ---------- figure pieces ----------


def mark(r: dict, cls: str, name: str) -> str:
    """One lane: interval whisker plus a dot or bar end, positioned in percent of 0-100%."""
    tip = esc(f"{name}: {pct(r['rate'])} (95% CI {ci(r)}), n = {r['n']:,} sentences")
    return (
        f'<div class="lane {cls}" title="{tip}">'
        f'<span class="ci" style="left:{r["lo"] * 100:.2f}%;width:{(r["hi"] - r["lo"]) * 100:.2f}%"></span>'
        f'<span class="dot" style="left:{r["rate"] * 100:.2f}%"></span>'
        f"</div>"
    )


def bar(r: dict, name: str) -> str:
    tip = esc(f"{name}: {pct(r['rate'])} (95% CI {ci(r)}), n = {r['n']:,} sentences")
    return (
        f'<div class="lane bar" title="{tip}">'
        f'<span class="fill" style="width:{r["rate"] * 100:.2f}%"></span>'
        f'<span class="ci" style="left:{r["lo"] * 100:.2f}%;width:{(r["hi"] - r["lo"]) * 100:.2f}%"></span>'
        f"</div>"
    )


def value(r: dict) -> str:
    return f'<span class="v">{pct(r["rate"])}</span><span class="i">{ci(r)}</span>'


AXIS = (
    '<div class="row axis" aria-hidden="true"><div class="lab"></div>'
    '<div class="track"><span style="left:0">0</span><span style="left:25%">25</span>'
    '<span style="left:50%">50</span><span style="left:75%">75</span>'
    '<span style="left:100%">100%</span></div><div class="val"></div></div>'
)


def table(head: list[str], rows: list[list[str]]) -> str:
    th = "".join(f"<th>{h}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return (
        f'<details class="tv"><summary>Table view</summary>'
        f"<table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></details>"
    )


def figure(fid: str, caption: str, rows: str, tbl: str, legend: str = "", source: str = "") -> str:
    src = f'<p class="src">Source: {source}</p>' if source else ""
    return (
        f'<figure id="{fid}"><figcaption>{caption}</figcaption>{legend}'
        f'<div class="plot">{rows}{AXIS}</div>{src}{tbl}</figure>'
    )


def bars_figure(fid, caption, items, source, label_head=""):
    """items: (label_html, sub_html, row, name)."""
    rows, trows = [], []
    for label, sub, r, name in items:
        subhtml = f'<div class="sub">{sub}</div>' if sub else ""
        rows.append(
            f'<div class="row"><div class="lab">{label}{subhtml}</div>'
            f'<div class="track">{bar(r, name)}</div><div class="val">{value(r)}</div></div>'
        )
        trows.append([label, pct(r["rate"]), ci(r), f"{r['n']:,}"])
    tbl = table([label_head, "Rate", "95% CI", "Sentences"], trows)
    return figure(fid, caption, "".join(rows), tbl, source=source)


def pair_figure(fid, caption, measures, a, b, a_name, b_name, cls_a, cls_b, source, legend):
    """Two lanes per measure. measures: (key, label_html)."""
    rows, trows = [], []
    for key, label in measures:
        ra, rb = a[key], b[key]
        rows.append(
            f'<div class="row pair"><div class="lab">{label}</div>'
            f'<div class="track">{mark(ra, cls_a, a_name)}{mark(rb, cls_b, b_name)}</div>'
            f'<div class="val"><div>{value(ra)}</div><div>{value(rb)}</div></div></div>'
        )
        trows.append([label, f"{pct(ra['rate'])} ({ci(ra)})", f"{pct(rb['rate'])} ({ci(rb)})"])
    tbl = table(["Measure", a_name, b_name], trows)
    return figure(fid, caption, "".join(rows), tbl, legend=legend, source=source)


def legend(items: list[tuple[str, str]]) -> str:
    li = "".join(f'<li><span class="key {cls}"></span>{esc(name)}</li>' for cls, name in items)
    return f'<ul class="legend">{li}</ul>'


def group_figure(fid, caption, groups, source):
    """groups: (heading_html, [(label, row, name)])."""
    parts, trows = [], []
    for heading, items in groups:
        parts.append(f'<div class="ghead">{heading}</div>')
        for label, r, name in items:
            parts.append(
                f'<div class="row"><div class="lab">{label}'
                f'<div class="sub">{r["articles"]:,} articles</div></div>'
                f'<div class="track">{mark(r, "ink", name)}</div><div class="val">{value(r)}</div></div>'
            )
            trows.append([heading, label, pct(r["rate"]), ci(r), f"{r['articles']:,}"])
    tbl = table(["Measure", "Group", "Rate", "95% CI", "Articles"], trows)
    return figure(fid, caption, "".join(parts), tbl, source=source)


# ---------- data ----------

ts = load("overall_by_text_source")
news = {m: ts[("newsroom", m)] for (_, m) in ts if _ == "newsroom"}
police = {m: ts[("police_matched", m)] for (_, m) in ts if _ == "police_matched"}
hb = load("headline_vs_body")
iv = load("initial_vs_follow_up")
ow = load("outlet_without_wire")
cities = load("compare_cities")
infra = load("v15m_infra_by_source")
transit = load("v15m_transit_by_source")
dm = load("driver_mentioned_by_exceptional")

with open(TABLES / "ksi_coverage.csv") as f:
    ksi = {(r["group"], r["value"]): r for r in csv.DictReader(f)}

with open(ROOT / "eval" / "reports" / "metrics_summary.csv") as f:
    metrics = {
        r["label"]: r
        for r in csv.DictReader(f)
        if r["system"] == "rule" and r["sample"] == "random"
    }

n_news = news["voice_active"]["n"]
named = news["driver_ref_vehicle"]["rate"] + news["driver_ref_person"]["rate"]
vehicle_share = news["driver_ref_vehicle"]["rate"] / named
no_agent = sum(
    news[m]["rate"] for m in ("voice_agentless_passive", "voice_intransitive", "voice_nominal")
)

# ---------- figures ----------

VOICE = [
    ("voice_active", "active", "A dump truck hit a cyclist."),
    ("voice_passive_with_agent", "passive_with_agent", "A cyclist was struck by a car."),
    ("voice_agentless_passive", "agentless_passive", "A cyclist was struck near Spadina Avenue."),
    ("voice_intransitive", "intransitive", "A cyclist and a car collided at Harbord and Spadina."),
    ("voice_nominal", "nominal", "A cyclist is in hospital following a crash."),
]

fig_voice = bars_figure(
    "fig-voice",
    f"Share of newsroom crash sentences in each voice form, first reports (n&nbsp;=&nbsp;{n_news:,}). "
    "Bars show the rate, whiskers the 95% interval. Example sentences are constructed, from the codebook.",
    [(code(lab), f"“{esc(ex)}”", news[m], lab) for m, lab, ex in VOICE],
    link("analysis/tables/overall_by_text_source.csv"),
    label_head="Voice",
)

DRIVER = [
    ("driver_ref_person", "person", "a driver, a motorist"),
    ("driver_ref_vehicle", "vehicle", "a car, an SUV, a truck"),
    ("driver_ref_absent", "absent", "neither appears in the impact clause"),
]

fig_driver = bars_figure(
    "fig-driver",
    "How the impact clause refers to whoever struck the pedestrian or cyclist, newsroom crash sentences in first reports.",
    [(code(lab), esc(desc), news[m], lab) for m, lab, desc in DRIVER],
    link("analysis/tables/overall_by_text_source.csv"),
    label_head="driver_reference",
)

SOURCE_MEASURES = [
    ("voice_active", code("voice = active")),
    ("voice_passive_with_agent", code("voice = passive_with_agent")),
    ("driver_ref_person", code("driver_reference = person")),
    ("driver_ref_vehicle", code("driver_reference = vehicle")),
    ("driver_ref_absent", code("driver_reference = absent")),
    ("focus_vru", code("focus = vru")),
]

fig_source = pair_figure(
    "fig-source",
    f"Newsroom sentences (n&nbsp;=&nbsp;{n_news:,}) against sentences that closely restate a linked "
    f"Toronto Police release (n&nbsp;=&nbsp;{police['voice_active']['n']}), first reports. "
    f"<code>focus</code> is the least reliable rule (macro-F1 {float(metrics['focus']['macro_f1']):.2f}; "
    'see <a href="#checks">checks</a>).',
    SOURCE_MEASURES,
    news,
    police,
    "Newsroom",
    "Police-matched",
    "s1",
    "s2",
    link("analysis/tables/overall_by_text_source.csv"),
    legend([("s1", "Newsroom"), ("s2", "Police-matched")]),
)

head = {m: hb[("headline", m)] for (g, m) in hb if g == "headline"}
body = {m: hb[("body", m)] for (g, m) in hb if g == "body"}
fig_headline = pair_figure(
    "fig-headline",
    f"Headlines (n&nbsp;=&nbsp;{head['voice_active']['n']:,}) against body crash sentences outside quotation marks "
    f"(n&nbsp;=&nbsp;{body['voice_active']['n']:,}), first reports only. "
    f"<code>focus</code> is the least reliable rule (macro-F1 {float(metrics['focus']['macro_f1']):.2f}; "
    'see <a href="#checks">checks</a>).',
    [
        ("voice_passive_with_agent", code("voice = passive_with_agent")),
        ("focus_vru", code("focus = vru")),
        ("voice_active", code("voice = active")),
    ],
    head,
    body,
    "Headlines",
    "Body",
    "ink hollow",
    "ink",
    link("analysis/tables/headline_vs_body.csv"),
    legend([("ink hollow", "Headlines"), ("ink", "Body")]),
)

init = {m: iv[("initial", m)] for (g, m) in iv if g == "initial"}
foll = {m: iv[("follow_up", m)] for (g, m) in iv if g == "follow_up"}
fig_follow = pair_figure(
    "fig-follow",
    f"First reports (n&nbsp;=&nbsp;{init['voice_active']['n']:,} sentences) against follow-up articles "
    f"(n&nbsp;=&nbsp;{foll['voice_active']['n']}): later articles about the same crash, such as a victim being identified or a vigil. "
    "Quoted text excluded.",
    [
        ("voice_active", code("voice = active")),
        ("driver_ref_vehicle", code("driver_reference = vehicle")),
    ],
    init,
    foll,
    "First reports",
    "Follow-ups",
    "ink",
    "ink hollow",
    link("analysis/tables/initial_vs_follow_up.csv"),
    legend([("ink", "First reports"), ("ink hollow", "Follow-ups")]),
)

OUTLETS = [("citynews", "CityNews Toronto"), ("ctv", "CTV News Toronto"), ("global", "Global News")]
fig_outlets = group_figure(
    "fig-outlets",
    "Body crash sentences by outlet, January 2025 to October 2026, the window all three outlets cover. "
    "Wire stories excluded. Three of the twelve body measures are shown; the table holds all of them.",
    [
        (
            heading,
            [(name, ow[(key, m)], f"{name}, {lab}") for key, name in OUTLETS],
        )
        for m, heading, lab in [
            ("driver_ref_vehicle", code("driver_reference = vehicle"), "driver as vehicle"),
            ("voice_nominal", code("voice = nominal"), "nominal voice"),
            ("voice_active", code("voice = active"), "active voice"),
        ]
    ],
    link("analysis/tables/outlet_without_wire.csv"),
)


def non_overlapping(t):
    """(measure, outlet, outlet) pairs whose intervals do not overlap."""
    out = set()
    names = [k for k, _ in OUTLETS]
    for (o, m), r in t.items():
        for o2 in names[names.index(o) + 1 :]:
            r2 = t[(o2, m)]
            if r["lo"] > r2["hi"] or r2["lo"] > r["hi"]:
                out.add((m, o, o2))
    return out


# The prose below names these differences; fail the build if the tables change under it.
assert non_overlapping(ow) == {
    ("driver_ref_vehicle", "citynews", "ctv"),
    ("voice_nominal", "citynews", "ctv"),
}, non_overlapping(ow)
oh = load("outlet_headlines")
assert non_overlapping(oh) == {
    ("driver_ref_vehicle", "citynews", "ctv"),
    ("driver_ref_person", "citynews", "ctv"),
    ("driver_hidden", "citynews", "ctv"),
}, non_overlapping(oh)

CITIES = [
    ("toronto_en", "Toronto (CityNews, CTV, Global)"),
    ("vancouver_en", "Vancouver, English"),
    ("montreal_en", "Montreal, English"),
    ("montreal_fr", "Montreal, French (Radio-Canada)"),
]
fig_cities = group_figure(
    "fig-cities",
    "Share of crash sentences that do not name a driver (driver is the "
    + code("vehicle")
    + " or "
    + code("absent")
    + "). Body sentences of first reports, quoted text excluded, police-matched text included.",
    [("Driver not named", [(name, cities[(key, "driver_hidden")], name) for key, name in CITIES])],
    link("analysis/tables/compare_cities.csv"),
)

SOURCES = [
    ("quoted", code("quoted")),
    ("attributed", code("attributed")),
    ("newsroom", code("newsroom")),
]


def stance_figure(fid, caption, t, prefix, source):
    sup = {k: t[(k, f"{prefix}_support")] for k, _ in SOURCES}
    opp = {k: t[(k, f"{prefix}_oppose")] for k, _ in SOURCES}
    return pair_figure(
        fid,
        caption,
        SOURCES,
        sup,
        opp,
        "Support",
        "Oppose",
        "ink",
        "ink hollow",
        source,
        legend([("ink", "Support"), ("ink hollow", "Oppose")]),
    )


fig_infra = stance_figure(
    "fig-infra",
    "Bike infrastructure: share of sentences naming it that report support or opposition, by text source "
    f"(n&nbsp;=&nbsp;{infra[('quoted', 'stance_infrastructure_any')]['n']}, "
    f"{infra[('attributed', 'stance_infrastructure_any')]['n']}, "
    f"{infra[('newsroom', 'stance_infrastructure_any')]['n']}).",
    infra,
    "stance_infrastructure",
    link("analysis/tables/v15m_infra_by_source.csv"),
)
fig_transit = stance_figure(
    "fig-transit",
    "Transit: share of sentences naming it that report support or opposition, by text source "
    f"(n&nbsp;=&nbsp;{transit[('quoted', 'stance_transit_any')]['n']}, "
    f"{transit[('attributed', 'stance_transit_any')]['n']}, "
    f"{transit[('newsroom', 'stance_transit_any')]['n']}).",
    transit,
    "stance_transit",
    link("analysis/tables/v15m_transit_by_source.csv"),
)

exc, orda = dm[("exceptional", "driver_ever_mentioned")], dm[("ordinary", "driver_ever_mentioned")]
k_all, k_fatal, k_ser = ksi[("all", "all")], ksi[("severity", "fatal")], None
for (g, v), r in ksi.items():
    if g == "severity" and v != "fatal":
        k_ser = r


def kpct(r):
    return f"{float(r['rate']) * 100:.0f}% ({float(r['ci_lo']) * 100:.0f}–{float(r['ci_hi']) * 100:.0f})"


def mrow(label, name):
    m = metrics[label]
    return [
        code(name),
        m["n"],
        f"{float(m['accuracy']):.2f}",
        f"{float(m['macro_f1']):.2f}",
        f"{float(m['macro_f1_lo']):.2f}–{float(m['macro_f1_hi']):.2f}",
    ]


eval_rows = "".join(
    "<tr>" + "".join(f"<td>{c}</td>" for c in mrow(lbl, lbl)) + "</tr>"
    for lbl in ("voice", "driver_reference", "focus", "text_source")
)

# ---------- page ----------

PAGE = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crash Framing in Toronto News</title>
<meta name="description" content="How Toronto news describes crashes involving pedestrians and cyclists, measured sentence by sentence, and a browser extension that labels crash sentences on the page you are reading.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="masthead">
  <p class="kicker">Media framing study · Toronto, 2023–2026</p>
  <h1>How Toronto news describes crashes involving pedestrians and cyclists</h1>
  <p class="lede">In newsroom-written crash sentences from CityNews, CTV and Global, the person struck is usually the grammatical subject and the vehicle is usually the agent. Half of these sentences ({pct(news["voice_passive_with_agent"]["rate"])}, 95% CI {ci(news["voice_passive_with_agent"])}) are passives like “a cyclist was struck by a car.” When the sentence names whoever struck the person, it names the vehicle rather than the driver {vehicle_share * 100:.0f}% of the time. Sentences that restate Toronto Police releases use the active voice more often than the newsroom's own sentences. In an LLM-annotated sample of bike lane and transit coverage, the positions reported almost always belong to sources, not to the outlets.</p>
  <p class="meta">The corpus holds 979 in-scope crash articles from January 2023 to October 2026. Rates use each outlet's first report on a crash, with wire copy counted once: {n_news:,} newsroom crash sentences from {news["voice_active"]["articles"]:,} articles. Crash labels come from grammar rules, shown with their evidence; bike lane and transit stance labels came from an LLM annotator. Test labels came from an LLM annotator, not a human (<a href="#checks">what that limits</a>).</p>
  <nav class="toc" aria-label="Contents">
    <a href="#forms">Five ways to write a crash</a>
    <a href="#source">Where the wording comes from</a>
    <a href="#other">Comparisons</a>
    <a href="#bike">Bike lanes and transit</a>
    <a href="#checks">How the labels were checked</a>
    <a href="#extension">Browser extension</a>
  </nav>
</header>

<main>
<section id="forms">
  <h2>Five ways to write the same crash</h2>
  <p>The codebook sorts every crash sentence by the grammar of its impact clause. The forms differ in who acts. In the active voice a vehicle or driver is the subject that does the striking. In a passive the person struck is the subject, and the vehicle moves into a “by” phrase or drops out. Intransitive and nominal sentences describe a collision without anyone striking anyone.</p>
  {fig_voice}
  <p>Together, the three forms with no agent ({code("agentless_passive")}, {code("intransitive")}, {code("nominal")}) make up {no_agent * 100:.0f}% of newsroom crash sentences. Ralph et al. (2019) found “one-third” in US local news. The word “accident” appears in {pct(news["accident_term"]["rate"])} ({ci(news["accident_term"])}) of crash sentences, far below the 47% Ralph et al. reported. That gap was checked against the raw text: most remaining uses are charge names such as “leaving the scene of an accident.”</p>
  {fig_driver}
  <p>Counting only sentences that name someone or something as the striker, the vehicle is named {vehicle_share * 100:.0f}% of the time. Ralph et al. found 81%. Across whole articles the driver is usually present somewhere: {pct(orda["rate"])} ({ci(orda)}) of ordinary crash reports mention a driver, and {pct(exc["rate"])} ({ci(exc)}) of reports where the driver fled, was impaired or was charged. Those intervals overlap, so this corpus does not show the “rogue driver” gap described by Fevyer and Aldred (2022).</p>
</section>

<section id="source">
  <h2>Where the wording comes from</h2>
  <p>Every crash sentence is tagged by where its wording comes from: <em>quoted</em> (inside quotation marks), <em>police-matched</em> (close to the text of a linked Toronto Police release), or <em>newsroom</em> (everything else). The tag is assigned in that order. Quoted text is scored separately and left out of the rates above.</p>
  {fig_source}
  <p>Police-matched sentences use the active voice about three times as often as newsroom sentences ({pct(police["voice_active"]["rate"])} against {pct(news["voice_active"]["rate"])}; the intervals do not overlap) and name the vehicle as the striker less often. One limit: only 218 articles could be linked to a release, and those articles are more often about fatal and hit-and-run crashes than the rest, so the comparison holds for that subset. Only about 42% of releases in the period survive in the Wayback Machine, so some newsroom sentences may restate releases the project could not see.</p>
</section>

<section id="other">
  <h2>Comparisons: headlines, follow-ups, outlets and cities</h2>
  <h3>Headlines use the passive with an agent more often</h3>
  {fig_headline}
  <h3>Follow-up articles are more often active</h3>
  {fig_follow}
  <h3>Outlets overlap on most measures; CityNews and CTV differ on a few</h3>
  <p>Of 72 outlet comparisons (12 measures, three pairs of outlets, body text and headlines), 5 have intervals that do not overlap, all CityNews against CTV. In body text, CityNews named the vehicle as the striker more often, {rc(ow[("citynews", "driver_ref_vehicle")])} against {rc(ow[("ctv", "driver_ref_vehicle")])}, and wrote fewer nominal sentences, {rc(ow[("citynews", "voice_nominal")])} against {rc(ow[("ctv", "voice_nominal")])}. In headlines, CityNews named the vehicle more often, {rc(oh[("citynews", "driver_ref_vehicle")])} against {rc(oh[("ctv", "driver_ref_vehicle")])}, and the driver as a person less often, {rc(oh[("citynews", "driver_ref_person")])} against {rc(oh[("ctv", "driver_ref_person")])}. With this many comparisons, a few gaps can arise by chance. Global has only 31 articles in the common window, so its intervals are wide. The Toronto Sun, blogTO, Toronto Today and CBC were planned but could not be collected within their terms or robots.txt, so these outlets cover a narrow range of editorial positions.</p>
  {fig_outlets}
  <h3>Vancouver coverage leaves the driver unnamed less often</h3>
  {fig_cities}
  <p>Vancouver crash sentences left the driver unnamed less often than Toronto's; the intervals do not overlap. Montreal's English coverage is close to Toronto's. These are rule labels, tuned on Toronto text and not checked by hand in the other cities. Canadian Cycling Magazine's Toronto crash reports left the driver unnamed in 59% (44–72) of crash sentences, from only 13 articles.</p>
</section>

<section id="bike">
  <h2>Bike lanes and transit: positions belong to sources</h2>
  <p>In coverage of bike lanes and transit, the outlets almost never state a position in their own voice. Across the annotated sample of about 1,600 sentences, 511 state a position and 7 of those give it as the outlet's own: 5 of CityNews's 450 body sentences that name bike infrastructure (CTV 0 of 212, Global 0 of 293), and one transit sentence each at CityNews and Global.</p>
  <p class="caveat-inline">These stance labels came from an LLM annotator reading the codebook, not from a trained model, and no human checked them. A second run of the same model on 100 sentences agreed with kappa 0.94 for bike infrastructure and 1.0 for transit, which is self-consistency, not accuracy. No stance model passed validation.</p>
  <p>Positions from sources are common, especially on bike lanes. For this study the newsroom text is split by who is speaking: {code("quoted")} sentences sit inside quotation marks, {code("attributed")} sentences report what a named source said without quoting it, and {code("newsroom")} is the rest. Police matching is not used here. {code("newsroom")} sentences with a position still mostly report what a person or group said, because the attribution detector misses about a quarter of reported speech.</p>
  {fig_infra}
  {fig_transit}
  <p>CityNews bike-lane sentences carry a source's position more often than at least one other outlet in each text source; for quoted sentences, 80% (71–88) against 54% (38–68) at CTV. This is a difference in which positions get reported, not in the outlets' own views. In {code("newsroom")} bike-lane sentences the most common policy frame is law, at 39% (33–45). Across the periods of Ontario's Bill 212, legal framing was 19% before the plan, 33% at its announcement, 55% while the law was in force, 64% under the court injunction, 47% after the law was struck down and 31% after the appeal was allowed. Some periods hold fewer than 30 sentences; the {link("docs/writeup.md", "write-up")} gives the intervals.</p>
</section>

<section id="checks">
  <h2>How the labels were checked</h2>
  <div class="caveat">
    <p><strong>The test labels came from an LLM annotator, not a human.</strong> A Claude Code subagent, given only the codebook and the raw sentences, labeled the test set. Accuracy below measures agreement with that model's reading of the codebook. A second run of the same model gave the same crash labels on every shared sentence. That is self-consistency: it shows the codebook gives that model stable answers, not that independent people would agree. The pipeline itself uses no LLM API.</p>
  </div>
  <table class="eval">
    <thead><tr><th>Label</th><th>n</th><th>Accuracy</th><th>F1</th><th>95% CI</th></tr></thead>
    <tbody>{eval_rows}</tbody>
  </table>
  <p class="note">Random test rows only; F1 is macro-averaged over each label's values. Voice detection was also checked on human-labeled public data (UD English EWT passives: F1 0.85). Two labels, {code("thematic_cue")} and {code("vru_conduct_detail")}, did not reach a usable accuracy across the corpus, so the article rates built from them are not reported as findings.</p>
  <h3>Coverage against police-reported crashes</h3>
  <p>The corpus covers a minority of serious crashes. Of the police-reported pedestrian and cyclist crashes that killed or seriously injured someone (City of Toronto KSI open data), {kpct(k_all)} got a first report in the corpus: {kpct(k_fatal)} of fatal crashes and {kpct(k_ser)} of serious-injury crashes. These are lower bounds, since a report has to name both streets of the crash location to link.</p>
  <p>Every judgment call is logged in {link("DECISIONS.md")}, and label definitions are in {link("codebook.md")}. Scope rules were tightened after annotators found US wire stories and car-only crashes in the sample, which cut the corpus from 1,671 to 942 articles before later collection.</p>
</section>

<section id="extension">
  <h2>Label crash sentences while you read</h2>
  <p>The browser extension lists the crash sentences on the page you are reading, with each label and the rule evidence behind it. It uses the same rules as the study. It gives no article score or grade. For sentences outside quotation marks it shows suggestions based on the Road Collision Reporting Guidelines, marked as suggestions, not measured results.</p>
  <div class="ext">
    <ol class="steps">
      <li><span>Get the code and set up Python 3.11.</span>
<pre class="cmd"><code><span class="ln">git clone {REPO}.git</span><span class="ln">cd media-bias</span><span class="ln">python3.11 -m venv .venv &amp;&amp; . .venv/bin/activate</span><span class="ln">pip install -e ".[dev]"</span><span class="ln">python -m spacy download en_core_web_trf</span><span class="ln">python -m spacy download en_core_web_sm</span></code></pre></li>
      <li><span>Start the scoring server and leave it running.</span>
<pre class="cmd"><code><span class="ln">python -m app.score_server</span></code></pre>
      It listens on <code>127.0.0.1:8765</code> only and answers only browser extensions. Page text is scored in memory and never saved.</li>
      <li><span>Load the extension in Chrome or another Chromium browser.</span> Open <code>chrome://extensions</code>, turn on Developer mode, choose <em>Load unpacked</em>, and pick the <code>extension/</code> folder.</li>
      <li><span>Open a news article and click the extension's toolbar button</span>, then <em>Label this page</em>. Hover a label to see its evidence. Pages marked as French (<code>&lt;html lang="fr"&gt;</code>) use the French rules, which need <code>python -m spacy download fr_core_news_sm</code> and <code>fr_dep_news_trf</code>.</li>
    </ol>
    <figure class="shot">
      <img src="popup.png" width="444" height="671" alt="The extension popup listing crash sentences from a test article. Each sentence has tags such as voice: passive_with_agent and driver_reference: vehicle, a quoted sentence is tagged quoted, and yellow boxes hold suggestions marked as not measured results.">
      <figcaption>The popup on a constructed test article. Hovering a tag such as <code>voice: passive_with_agent</code> shows the rule evidence, here “passive ‘struck’ + by-agent ‘vehicle’.”</figcaption>
    </figure>
  </div>
</section>
</main>

<footer>
  <p>Code, labels and aggregate tables: <a href="{REPO}">{REPO.removeprefix("https://")}</a>. Article text is not published. Full results and limitations: {link("docs/writeup.md", "write-up")}. Prior study: Ralph, Iacobucci, Thigpen and Goddard (2019), “Editorial patterns in bicyclist and pedestrian crash reporting,” <em>Transportation Research Record</em> 2673(2).</p>
</footer>
</body>
</html>
"""

(Path(__file__).parent / "index.html").write_text(PAGE)
print("wrote site/index.html")
