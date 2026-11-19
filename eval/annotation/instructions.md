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
