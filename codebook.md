# Codebook: crash framing (v1.0)

Status: v1.0, frozen for Phase 2 (2026-11-19). Every example sentence is **synthetic**, written to illustrate a rule. Synthetic examples keep article text out of the repo and out of the Qwen prompts, so no test sentence can leak into a prompt.

This file is the source of truth for labels. Code must not add, rename, or redefine a label without changing this file first. Decisions that resolved earlier ambiguities are tagged with their `DECISIONS.md` entry, for example (D-03).

Labels follow the five dimensions shared across the crash-reporting literature: focus, agency, grammatical voice, language, and narrative framing. Mappings to prior studies are in `docs/related-work.md`.

## 0. Scope and terms

- **In-scope crash:** a motor vehicle (car, SUV, truck, van, bus, TTC bus, streetcar, motorcycle) struck at least one pedestrian or cyclist. Fatal or non-fatal. Car-only crashes are out. A cyclist striking a pedestrian is out (D-01).
- **VRU:** vulnerable road user. Pedestrians include wheelchair and mobility-device users. Cyclists include e-bike and e-scooter riders. Motorcyclists are not VRUs (D-01).
- **Impact verbs** (lemmas): hit, strike, run over, collide, crash (into), knock down, mow down, pin, drag, clip, door, back into, plow into, slam into, ram (D-02).
- **Collision nouns:** crash, collision, accident (D-03).
- **Impact clause:** the clause whose main predicate is the first impact verb in sentence order. If the sentence has no impact verb, the main clause.
- Headlines and body sentences get the same labels and are scored separately.

## 1. Sentence filter

### 1.1 `crash_sentence` (yes / no)

**Definition.** The sentence describes the collision itself: it contains an impact verb or a collision noun, plus at least one road user (pedestrian, cyclist, driver, or vehicle).

**Decision rules.**
- Excluded even if a road user is present: road closures, the investigation, witness or dashcam appeals, hospital transport, and death or injury reports, unless the same sentence also mentions the collision.
- A collision noun with no road user ("The crash happened around 9 p.m.") is excluded.
- "A cyclist died" alone is excluded (no impact verb or collision noun). "A cyclist died after the crash" is included (D-04).

**Positive.** "A cyclist was struck by a driver at Bloor Street and Spadina Avenue on Tuesday." / "A pedestrian is dead after a collision with a TTC bus in Scarborough."

**Negative.** "Police closed Bloor Street between Spadina and Bathurst for the investigation." / "The victim was taken to a trauma centre with life-threatening injuries."

### 1.2 `vru_sentence` (yes / no)

**Definition.** Any body sentence in a crash article that mentions a VRU (by role noun, description, name, or pronoun linked by coreference). Used only as the unit for `vru_conduct_detail` (D-10).

**Positive.** "The cyclist was not wearing a helmet." / "She was crossing the street with her dog."

**Negative.** "The road reopened around 6 a.m." / "The driver stayed at the scene."

## 2. Sentence labels (crash sentences, except 2.6)

### 2.1 `voice`

Values: `active`, `passive_with_agent`, `agentless_passive`, `intransitive`, `nominal`. Computed on the impact clause. `intransitive` and `nominal` are reported separately and never merged into `agentless_passive`.

| Value | Definition |
|---|---|
| `active` | Active impact verb with the striking party as subject and the struck party as object or prepositional object ("crashed into a cyclist"). |
| `passive_with_agent` | Passive impact verb with the striking party in a "by" phrase. |
| `agentless_passive` | Passive impact verb with no "by" phrase. |
| `intransitive` | Impact verb with no struck road user as object: "a car crashed", "the SUV crashed into a pole", "a cyclist and a car collided" (D-05). |
| `nominal` | No impact verb; the collision appears only as a noun ("Pedestrian dead after collision"). |

**Decision rules (D-05).**
- Impact verb present → label it by its form. No impact verb, but a collision noun → `nominal`.
- Get-passives ("got hit") and reduced passives with no auxiliary ("Cyclist struck by car on Bloor") are passives.
- If the impact verb sits in a subordinate clause ("Police say a car hit a cyclist"), label that clause.
- Two impact clauses → label the first in sentence order.
- "A cyclist died after being struck" → `agentless_passive` (the impact clause is "being struck").

| Value | Positive | Negative |
|---|---|---|
| `active` | "A driver struck a cyclist on Queen Street West." / "An SUV hit a pedestrian at Yonge and Eglinton." | "A cyclist was struck by a driver." / "A pedestrian was hit near Dundas Square." |
| `passive_with_agent` | "A pedestrian was hit by a pickup truck in North York." / "Cyclist struck by streetcar on King Street." | "A pedestrian was hit in North York." / "A pickup truck hit a pedestrian." |
| `agentless_passive` | "A cyclist was struck near Spadina Avenue on Monday night." / "A woman, 70, died after being hit while crossing Lawrence Avenue East." | "A woman, 70, was hit by a driver on Lawrence Avenue East." / "A cyclist is dead after a collision on Bloor." |
| `intransitive` | "A cyclist and a car collided at Harbord and Spadina." / "An SUV crashed into a bus shelter on Lawrence Avenue, injuring a pedestrian." | "The car crashed into a pedestrian." / "A cyclist was struck on Danforth Avenue." |
| `nominal` | "Pedestrian dead after collision in Etobicoke." / "A cyclist is in hospital following a crash involving a dump truck." | "A dump truck hit a cyclist." / "A cyclist was hit." |

### 2.2 `driver_reference`

Values: `person`, `vehicle`, `absent`. Computed on the impact clause.

| Value | Definition |
|---|---|
| `person` | A human driver appears in the impact clause: role noun (driver, motorist, operator), person description ("a 34-year-old man"), pronoun linked to the driver, or name. |
| `vehicle` | No human driver; a vehicle appears in the impact clause, as agent or as the other party ("A cyclist collided with a car") (D-06). |
| `absent` | Neither a driver nor a vehicle appears in the impact clause. |

**Decision rules.**
- Precedence: any human driver in the impact clause → `person` ("the driver of a pickup struck…").
- "TTC bus operator" → `person`. "The TTC bus" and "the TTC" → `vehicle` (D-06).
- A driver mentioned only in another clause ("A cyclist was struck, and the driver stayed") does not count.

| Value | Positive | Negative |
|---|---|---|
| `person` | "The driver of a pickup truck struck a pedestrian." / "A man, 41, driving an SUV hit a cyclist." | "A pickup truck struck a pedestrian." / "A pedestrian was struck." |
| `vehicle` | "A car hit a cyclist on Bloor." / "A cyclist collided with a streetcar." | "A motorist hit a cyclist on Bloor." / "A cyclist was hit on Bloor." |
| `absent` | "A pedestrian was struck in Scarborough." / "Cyclist hit near High Park." | "A pedestrian was struck by a van in Scarborough." / "A driver hit a cyclist near High Park." |

### 2.3 `focus`

Values: `vru`, `driver`, `vehicle`, `other`. The grammatical subject of the impact clause.

**Decision rules.**
- Take the subject from the impact clause, not the reporting clause ("Police say a car hit a cyclist" → `vehicle`).
- `nominal` sentences: subject of the main clause ("Pedestrian dead after collision" → `vru`).
- Expletive or event subjects ("There was a collision", "The crash happened…") → `other`.
- Conjoined subject → category of the first conjunct ("A cyclist and a car collided" → `vru`) (D-07).

| Value | Positive | Negative |
|---|---|---|
| `vru` | "A cyclist was hit by a driver." / "A pedestrian was struck on Finch Avenue." | "A driver hit a cyclist." / "A car struck a pedestrian on Finch." |
| `driver` | "A driver struck a pedestrian on Jane Street." / "The motorist hit a cyclist and drove away." | "A pedestrian was struck by a driver on Jane Street." / "A van hit a cyclist." |
| `vehicle` | "A dump truck struck a cyclist on Bloor." / "A TTC bus hit a pedestrian at Kennedy station." | "A cyclist was struck by a dump truck." / "The truck driver struck a cyclist." |
| `other` | "There was a collision between a car and a cyclist at Dundas and Ossington." / "Police say a collision involving a pedestrian occurred overnight." | "A car and a cyclist collided at Dundas and Ossington." / "A pedestrian was hit overnight." |

### 2.4 `vru_as_actor` (yes / no)

**Definition.** The VRU is grammatically presented as an actor in the collision: subject (or first conjunct of the subject) of an impact verb, or head of "in collision with".

**Decision rules (D-08).**
- Yes: "A cyclist collided with a car", "pedestrian in collision with vehicle", "A cyclist and a car collided".
- No: the VRU is the object or passive subject of the impact verb.
- Movement without an impact verb ("stepped into the path of a vehicle") is not `vru_as_actor`; it is coded as `vru_conduct_detail`.

**Positive.** "A cyclist collided with a car at Harbord Street and Spadina." / "Police say a pedestrian was in collision with a vehicle on Eglinton."

**Negative.** "A car collided with a cyclist at Harbord Street." / "A pedestrian was struck by a vehicle on Eglinton."

### 2.5 `accident_term` (yes / no)

**Definition.** The sentence uses the noun "accident(s)" for the crash.

**Decision rules (D-09).**
- Lemma `accident` only. "Accidentally" and "accidental" are not counted. "Incident" and "mishap" are not counted.
- Proper names containing the word do not count.
- Because "accident" is a collision noun (D-03), sentences like "The accident happened at Queen and Spadina" reach this label when they name a road user.

**Positive.** "A cyclist was killed in an accident with a truck on Bloor." / "Police say the pedestrian was struck in a hit-and-run accident."

**Negative.** "A cyclist was killed in a crash with a truck on Bloor." / "Police say the pedestrian was struck in a hit-and-run collision."

### 2.6 `vru_conduct_detail` (yes / no), on `vru_sentence` units

**Definition.** The sentence gives a detail about the VRU's behaviour, appearance, or equipment that a reader could take as bearing on fault: helmet, clothing or visibility, headphones or phone, crossing location relative to a crosswalk or signal, crossing against a signal, sudden movement ("stepped into the path", "darted out").

**Decision rules (D-10).**
- Unit: every `vru_sentence` in a crash article, not only crash sentences, because conduct details usually sit in their own sentence. Also rolled up to the article as `vru_conduct_any`.
- Count the detail whichever way it points ("was wearing a helmet" and "was not wearing a helmet" both count).
- Location alone ("at Bloor and Spadina") is not conduct.
- Driver conduct is not coded here.

**Positive.** "The cyclist was not wearing a helmet, police said." / "A pedestrian crossing mid-block was hit by a van on Kingston Road."

**Negative.** "The cyclist was taken to hospital with serious injuries." / "A pedestrian was hit by a van at Kingston Road and Midland Avenue."

## 3. Derived sentence attributes

### 3.1 `text_source`

Deterministic, not a labeling target. Precedence `quoted` > `police_matched` > `newsroom`.

| Value | Definition |
|---|---|
| `quoted` | Direct speech: the impact clause (or, for a non-crash sentence, most of the sentence) is inside quotation marks (D-11). |
| `police_matched` | Not quoted, and similarity to the linked police release is above the threshold tuned on the dev set. |
| `newsroom` | Neither. |

Indirect speech ("Police say a car struck a cyclist") is **not** `quoted`. It goes through release matching, and a separate boolean `attributed` records that the sentence names a source (D-11).

| Value | Positive | Negative |
|---|---|---|
| `quoted` | "\"The vehicle struck the cyclist as she entered the intersection,\" Const. Smith said." / "\"It was an accident,\" a witness told reporters." | "Police say the vehicle struck the cyclist as she entered the intersection." / "Police said the driver 'remained at the scene' after a car hit a cyclist." (impact clause outside the quote) |
| `police_matched` | Release "It is reported that a vehicle was travelling eastbound on Bloor Street West and struck a cyclist." → article "A vehicle was travelling eastbound on Bloor Street West when it struck a cyclist." / release "The pedestrian was transported to hospital with serious injuries." → article "The pedestrian was taken to hospital with serious injuries." | "Cyclists have long called for a protected lane on this stretch." / "\"A vehicle struck a cyclist,\" police said." |
| `newsroom` | "It is the fourth cyclist death in Toronto this year." / "The intersection has no protected bike lane." | The two `police_matched` positives. |

## 4. Article labels

### 4.1 `driver_ever_mentioned` (yes / no)

**Definition.** Any sentence refers to a human driver: role noun (driver, motorist, operator), coreferent description, or name.

**Decision rules.**
- Primary count uses `newsroom` + `police_matched` sentences; a second count includes `quoted`.
- Any sentence counts, not only crash sentences. "The vehicle remained at the scene" does not count.
- Always reported split by `driver_exceptional`.

**Positive.** "A cyclist was struck on Bloor. … The driver, a 52-year-old man, remained at the scene." / "A pedestrian was hit by an SUV. … Police say the motorist was not injured."

**Negative.** "A cyclist was struck by a car on Bloor. … The vehicle remained at the scene." / "A pedestrian was hit by an SUV. … The victim was taken to hospital. … The road was closed for several hours."

### 4.2 `driver_exceptional` (yes / no)

**Definition.** The article describes the driver through exceptional behaviour: fled, impaired, a Criminal Code charge, or street racing / stunt driving.

**Decision rules (D-12).**
- Fled: "fled", "failed to remain", "hit-and-run", "drove away".
- Impaired: alcohol or drug impairment, stated or charged.
- Criminal Code charges: dangerous operation, impaired operation, criminal negligence, failure to stop after an accident.
- Street racing and stunt driving count.
- Highway Traffic Act charges (careless driving, failing to yield) do **not** count. They are recorded in a separate field `driver_hta_charge`.
- Speeding alone and a suspended licence alone do not count.

**Positive.** "The driver fled the scene and police are searching for a dark sedan." / "The driver, 29, was charged with impaired operation causing bodily harm."

**Negative.** "The driver remained at the scene and is cooperating with police." / "The driver was charged with careless driving under the Highway Traffic Act."

### 4.3 `thematic_frame` (yes / no)

**Definition.** The article mentions road design, crash trends, policy, statistics, or expert comment beyond the single episode. Computed from sentence-level `thematic_cue` (yes/no) on every body sentence; the article is thematic if any sentence is.

**Decision rules (D-13).**
- Counts: crash counts or rates, road design, policy (Vision Zero, speed limits, bike lanes), and any speaker (expert, advocate, politician) who refers to a cause, pattern, or fix beyond this crash.
- Does not count: details of this crash, police appeals, victim biography, a politician's condolences.

**Positive.** "It is the 12th pedestrian death on Toronto roads this year, according to police data." / "Advocates have called for a protected bike lane on this stretch of Bloor since 2019."

**Negative.** "Police are asking anyone with dashcam footage to come forward." / "The councillor said her thoughts are with the victim's family."

### 4.4 `police_overlap` (0–1, or null)

**Definition.** Share of the article's non-quoted body sentences with `text_source = police_matched` (D-14). Null when the article has no linked release, never zero.

**Positive (high).** A four-sentence brief with three sentences lightly edited from the release → 0.75. / A brief that copies the release's first two paragraphs → about 1.0.

**Negative (low or null).** A feature with interviews and one sentence from the release among 30 → about 0.03. / No linked release → null.

### 4.5 `severity`

Values: `fatal`, `injury`, `no_injury`, `unknown`. Recorded for both the article (what it reports when fetched) and the crash (the worst outcome across its articles) (D-15). "Life-threatening", "critical", "serious", "minor" → `injury`.

| Value | Positive | Negative |
|---|---|---|
| `fatal` | "A cyclist has died after being struck…" / "…was pronounced dead at the scene." | "…taken to hospital with life-threatening injuries." / "…sustained minor injuries." |
| `injury` | "…taken to hospital with serious injuries." / "…treated for minor injuries at the scene." | "…died in hospital." / "…was not injured." |
| `no_injury` | "No one was hurt." / "The cyclist was shaken but uninjured." | "…suffered a broken leg." / "…was killed." |
| `unknown` | "Police have not said whether anyone was hurt." / no injury information | Any of the above |

### 4.6 `road_users`

Multi-valued set: `pedestrian`, `cyclist`, `driver`, `transit_vehicle`. TTC bus or streetcar → `transit_vehicle`; add `driver` only if a driver or operator is mentioned (D-16). Articles without `pedestrian` or `cyclist` leave the crash set.

**Positive (`cyclist`, `transit_vehicle`).** "A cyclist was struck by a streetcar on King Street." / "A TTC bus hit a cyclist on Dufferin."

**Negative (for `cyclist`).** "A pedestrian was struck by a streetcar." / "A car hit a pedestrian on Dufferin."

### 4.7 `crash_id`

Links articles about the same crash: same date (± 1 day), same intersection or block, consistent road users.

**Same crash.** "A cyclist was struck on Bloor at Spadina Tuesday morning." and "Driver charged after cyclist hit at Bloor and Spadina on Tuesday."

**Different crash.** "A cyclist was struck at Bloor and Spadina on Tuesday." and "A cyclist was struck at Bloor and Bathurst on Tuesday."

### 4.8 `article_type`

Values: `initial`, `follow_up`, `roundup`. Primary analysis uses `initial`; `follow_up` is reported separately; `roundup` is excluded in v1.

**Decision rules (D-17).** `initial` is defined per outlet: the outlet's first article on the crash. Articles are labeled by the content fetched; the fetch timestamp is stored.

| Value | Positive | Negative |
|---|---|---|
| `initial` | "A cyclist is in hospital after being struck by a driver on Bloor on Tuesday morning." / "Police are investigating after a pedestrian was hit in Scarborough overnight." | "A driver has been charged in last week's crash that killed a cyclist." / "Three pedestrians were struck in separate collisions on Friday." |
| `follow_up` | "Police have identified the cyclist killed on Bloor last Tuesday." / "A vigil was held Sunday for the pedestrian killed on Finch." | The two `initial` positives |
| `roundup` | "Three pedestrians were struck in separate collisions across the city on Friday." / "Two cyclists were killed in Toronto this weekend." | The two `initial` positives |

## 5. Recorded exceptions (recorded, not penalized)

- Hit-and-run with an unknown driver: `driver_reference = absent` is expected. A `hit_and_run` flag is stored.
- Text inside quotation marks: scored separately via `text_source`.

## 6. Change log

- v1.0 (2026-11-19): resolved all draft flags (D-01 to D-17); added "accident" as a collision noun, the `vru_sentence` unit, `thematic_cue`, `attributed`, `driver_hta_charge`; extended the impact verb list.
