import pytest

from nlp.sources import article_sources, role_of, speaker_of


@pytest.mark.parametrize(
    "speaker,role",
    [
        ("Coun. Dianne Saxe", "politician_city"),
        ("the mayor's office", "politician_city"),
        ("Premier Doug Ford", "politician_province"),
        ("the transportation minister", "politician_province"),
        ("a TTC spokesperson", "agency_staff"),
        ("City staff", "agency_staff"),
        ("Const. Ali", "police"),
        ("Cycle Toronto", "vru_advocate"),
        ("a cyclist who rides the route daily", "vru_advocate"),
        ("one driver", "driver_group"),
        ("the Bloor-Annex BIA", "business"),
        ("a cafe owner", "business"),
        ("a University of Toronto researcher", "expert"),
        ("a rider at Kennedy station", "resident"),
        ("a resident", "resident"),
        ("the judge", "other"),
        ("one person", "unknown"),
    ],
)
def test_role_of(speaker, role):
    assert role_of(speaker) == role


def test_role_negatives():
    assert role_of("a business-school professor") == "expert"  # not business
    assert role_of("the TTC chair, Coun. Jamaal Myers") == "politician_city"  # not agency_staff
    assert role_of("a paramedic") == "other"  # not police


def test_speaker_of_patterns():
    assert speaker_of('"The lanes stay," Coun. Lee said.') == "Coun. Lee"
    assert speaker_of('"The bus never comes," said a rider at Kennedy station.') == (
        "a rider at Kennedy station"
    )
    assert speaker_of("The BIA says sales fell after the lanes went in.") == "The BIA"
    assert speaker_of("Sales fell, according to the Bloor-Annex BIA.") == "the Bloor-Annex BIA"
    assert speaker_of("The lanes opened in 2023.") is None


def test_article_sources_resolves_surnames_and_pronouns():
    sents = [
        "Premier Doug Ford announced the plan on Monday.",
        '"Drivers need relief," Ford said.',
        '"We will not back down," he added.',
        '"These lanes save lives," said Cycle Toronto executive director Ana Ruiz.',
        "The lanes opened in 2023.",
    ]
    out = article_sources(sents)
    roles = [(i, r) for i, _, r in out]
    assert roles == [(1, "politician_province"), (2, "politician_province"), (3, "vru_advocate")]


def test_role_cues_ignore_case():
    assert role_of("Mayor Tran") == "politician_city"
    assert role_of("Minister Okafor") == "politician_province"


def test_speaker_drops_leading_phrase_and_rejects_clauses():
    assert speaker_of("Asked about the cost, Tran said the city will pay.") == "Tran"
    assert speaker_of("The group said the law was arbitrary and dangerous.") == "The group"
    assert speaker_of("Critics said the price was double the installation cost.") == "Critics"
    assert speaker_of("He said the ruling was wrong.") == "He"


def test_bare_surname_takes_role_from_first_mention():
    sents = [
        "Priya Nandi, with Cycle Toronto, spoke at the rally.",
        "Nandi said the lanes save lives.",
        "Sam Ortiz, who owns a cafe on the street, disagreed.",
        '"Sales are down," Ortiz said.',
    ]
    out = article_sources(sents)
    assert [(i, r) for i, _, r in out] == [(1, "vru_advocate"), (3, "business")]


def test_more_roles_and_cleanup():
    assert role_of("the Ministry of Transportation") == "politician_province"
    assert role_of("NDP transport critic Ana Kim") == "politician_province"
    assert role_of("the city") == "agency_staff"
    assert role_of("The ruling") == "other"
    assert role_of("Uber driver Tom Li") == "driver_group"
    assert speaker_of("But Kim said the plan fails.") == "Kim"
    assert speaker_of('"It is wrong," Justice Reyes also wrote.') == "Justice Reyes"
    sents = ["Toronto mayor Mina Park opposed the bill.", '"We will fight it," Park said.']
    assert article_sources(sents)[0][2] == "politician_city"


def test_first_mention_uses_nearest_cue():
    sents = [
        "The province lost when Superior Court Justice Lena Moss ruled on Tuesday.",
        "Moss wrote that the law was arbitrary.",
    ]
    assert article_sources(sents)[0][2] == "other"


def test_role_cues_v2():
    assert role_of("officers") == "police"
    assert role_of("TPS Superintendent Ana Kim") == "police"
    assert role_of("the TTC's Chief Strategy Officer") == "agency_staff"  # not police
    assert role_of("TTC Chair Sam Lee") == "politician_city"
    assert role_of("Committee chair Ana Kim") == "politician_city"
    assert role_of("Rogers spokesperson Tom Li") == "business"
    assert role_of("Board of Trade president Ana Kim") == "business"
    assert role_of("GO") == "agency_staff"
    assert role_of("a transit user") == "resident"
    assert role_of("a principal at a mobility consulting firm") == "expert"


def test_document_speaker_takes_issuer_role():
    sents = [
        "Metrolinx released a report on the line's delays on Monday.",
        "The report said the project is two years behind schedule.",
    ]
    assert article_sources(sents)[0][2] == "agency_staff"


def test_speaker_trims_words_before_a_trailing_pronoun_or_name():
    # quality check 2026-11-22
    assert speaker_of("And sometimes, he just says three simple words.") == "he"
    assert speaker_of("What 2 things Bauer says the TTC could do better.") == "Bauer"
    assert speaker_of("He said the ruling was wrong.") == "He"


def test_spokesperson_takes_role_of_the_body_named_with_it():
    sents = [
        "A spokesperson for the TTC confirmed the closure.",
        "“The work will take a month,” a spokesperson said.",
    ]
    assert article_sources(sents)[-1][2] == "agency_staff"
