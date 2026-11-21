# Annotator instructions (given to each annotator subagent)

You are an independent annotator. You receive two inputs only: `codebook.md` and one
packet file of sentences (`data/eval/packet_<split>_<set>.jsonl`). Do not read any other
file in the repository: no code, no rule outputs, no model labels, no other packets.

Read `codebook.md` in full first. Apply its definitions literally. When a case is
unclear, use the codebook's decision rules and edge-case notes; do not invent new labels.

Each packet line has `sentence_id`, `sentence`, `headline` (true if it is a headline),
and for the text_source set, `police_release` (the linked Toronto Police release text).

Write one JSON object per input line to the output path you are given, with
`sentence_id` and the fields for the packet's set:

- **crash** set: `voice` (active | passive_with_agent | agentless_passive | intransitive |
  nominal), `driver_reference` (person | vehicle | absent), `focus` (vru | driver | vehicle |
  other), `vru_as_actor` (true | false), `accident_term` (true | false). If the sentence is
  not a crash-describing sentence under codebook §1, set every field to `not_crash`.
- **context** set: `vru_conduct_detail` (true | false), `thematic_cue` (true | false).
- **text_source** set: `text_source` (quoted | police_matched | newsroom), following the
  codebook precedence. `police_matched` means the sentence restates the release's content
  closely in wording (not just the same facts). If `police_release` is null, the sentence
  cannot be `police_matched`.

Label every line. Output valid JSONL only.

## v1.5 packets (codebook Part B)

- **v15** sentence packets (`packet_*_v15.jsonl`, lines with `sentence_id`, `sentence`,
  `headline`): label `policy_frame` (economic | safety | quality_of_life | political |
  legality | other | none), `stance_infrastructure` (support | oppose | none),
  `stance_cyclists` (positive | negative | none), `stance_transit` (support | oppose | none),
  following codebook §9. A sentence that names no target is `none` for that stance.
- **topic** packet (`packet_test_v15_topic.jsonl`, lines with `article_id`, `headline`,
  `lead`): label `bike_lane` and `transit` (true | false) under codebook §7.1, from the
  headline and lead only.
- **source** packet (`packet_test_v15_source.jsonl`, lines with `sentence_id`, `sentence`,
  `article`): give `speaker` (the person or body quoted or paraphrased in `sentence`, as the
  article names them) and `role` under codebook §8.1. Use the whole article to find how the
  speaker is introduced. If the sentence quotes no one, set both to `none`.
