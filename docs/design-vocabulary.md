# Design vocabulary

Reference for design decisions and critique on the project site (`site/`). Add to it when a review turns up a new failure.

## Principles, and why each works

- **Structure follows the content.** The project's unit is the sentence and its grammar, so the site is built around sentences and their labels. A reader learns the five voice forms once and then reads every later figure in those terms.
- **Result first.** Readers who stop after one paragraph should leave with the main finding and its uncertainty.
- **Uncertainty is part of the mark.** Every rate is drawn with its 95% interval. A bare number invites a ranking the data does not support.
- **Order by meaning, not by size.** Rows follow the codebook or a fixed list (outlets alphabetically, voice forms by grammar). Sorting by rate turns a description into a league table.
- **One color meaning per page.** Hue encodes text source (newsroom, police-matched) and nothing else. Other comparisons use ink and marker shape, so color never has to be relearned.
- **Codebook names stay visible.** Labels such as `passive_with_agent` appear in monospace exactly as in the codebook, the code and the extension, so a reader can trace a figure to its definition.
- **Caveats sit next to the claim they limit.** The LLM-annotator caveat appears where accuracy is reported, not only at the bottom.
- **Proximity carries relation** (Larkin and Simon). An example sentence sits on the same row as its rate; a figure sits directly under the sentence that states its point.

## Common failures

- A rate without an interval, or intervals drawn but ignored in the text.
- Claiming a difference where intervals overlap.
- Sorting categories by value, which implies a ranking.
- Several colors for one series, or one color meaning different things in different figures.
- Example sentences taken from real articles beyond a short excerpt (copyright), or presented as real when they are constructed.
- Charts whose axis does not start at zero for shares.
- Labels colliding, text overflowing at phone width, horizontal page scroll.
- Hover-only information with no table fallback.
- Claiming no difference when some intervals do not overlap. Check every pair against the table, and make the build fail if the prose and the table disagree.
- A count in the prose with a different denominator from the figure beside it.
- A 0–0 interval for a zero count, which reads as certainty. Use an upper bound (rule of three).
- A finding in the lede that rests on weaker labels than the rest, with no caveat beside it.
- Low contrast for muted text, especially in dark mode.

## Recognizable generic ("AI slop") patterns

- A hero section with a giant gradient headline and a vague tagline.
- Rows of three feature cards with emoji or line icons.
- Purple-to-blue gradients, glassmorphism, glowing shadows.
- Big stat tiles with no denominator or interval ("51%!").
- Pill badges and "Learn more" buttons on every section.
- Centered text everywhere; every section the same height and shape.
- Decorative illustrations unrelated to the data.
- Words like "unlock", "insights", "powerful", "seamless".
- Grades, scores or traffic-light colors that judge an outlet.
