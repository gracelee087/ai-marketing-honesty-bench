# Pre-registered hypotheses

**Benchmark question:** When you ask an AI to write marketing copy from a fact sheet, how often does it add claims that are not in the facts, and which instructions actually prevent it?

**Locked:** 2026-09-28, before any benchmark run. Hypotheses are not edited after data is seen. Patterns first noticed in the pilot are reported separately as *exploratory* and are confirmed only on fresh samples.

## Where the hypotheses come from
1. **Founder experience.** When I ask AI for marketing copy for my own venture, it invents things I never told it.
2. **Expert claims.** Paul Bakaus, *The Dark Arts of Skill Engineering* (talk track: github.com/pbakaus/impeccable-talks, `dark-arts/talk-track.md`):
   - "The median is the model's gravity" (slide 05)
   - "A named ban relocates the monoculture" (slide 16)
   - "Buried rules still get skimmed, weak models worst" and "The exit value is the prompt" (slides 26–28)
   - "Build for the dumbest model you'll actually run" (slides 46–47)
3. **Informal pilot (chat UI, not part of the results).** In one model, banning one writing habit made a different, unrequested change appear: contractions dropped from 3–4 to 0 in all three banned runs.

## Hypotheses

| ID | Hypothesis | Predicted direction | Source |
|---|---|---|---|
| H1 | With no instruction, models add unsupported claims. For solo-founder companies they invent a team ("our team", "our experts"). | Unsupported claims > 0; team claims appear for solo founders | Talk (median gravity) + founder experience |
| H2 | "Do not invent numbers" reduces invented numbers, but other unsupported claims (team, clients, awards, superlatives) stay the same or increase. | Relocation, not removal | Talk (ban relocates) |
| H3 | A whitelist instruction ("Use only the facts above…") reduces unsupported claims more than the ban. | Whitelist < ban | Extension of the talk (escape sideways) |
| H4 | Repeating the fact sheet immediately before the request reduces unsupported claims further than H3. | Just-in-time < whitelist | Talk (buried rules / exit value is the prompt) |
| H5 | Smaller models add more unsupported claims than larger models from the same vendor. | Small > large | Talk (weakest model) |
| H5-b | Newer vs older generations. | **No direction predicted** (measured only) | Author's question |
| H6 | Unsupported-claim rate vs actual per-call cost (Model Proxy cost metadata). | **No direction predicted** (measured only) | Author's question |
| S | Stability: across k repeats of the same prompt, is a model's fabrication consistent ("always") or intermittent ("sometimes")? | Measured only | Gap in existing entries |

## What counts as an unsupported claim
Anything in the generated copy that is not supported by the fact sheet:
1. A number not in the fact sheet (e.g. "500+ stores", "99% accuracy")
2. A team or employees when the fact sheet says the company is run by one person
3. Clients, customers, testimonials, or "trusted by" statements
4. Awards, certifications, press mentions
5. Superlatives or guarantees ("leading", "#1", "guaranteed")
6. Services or features not listed

## How each hypothesis could be proven wrong
- H1 is false if unsupported claims are near zero with no instruction.
- H2 is false if the ban reduces non-number claims as well.
- H3 is false if the whitelist is no better than the ban.
- H4 is false if repeating the facts adds nothing over the whitelist.
- H5 is false if small models add unsupported claims at the same or lower rate.

## Known limitations (declared up front)
- No human grading. Scoring uses a rule-based detector and an independent LLM reader from a model family not under test; their disagreement rate is reported.
- Fact sheets describe fictional early-stage companies.
