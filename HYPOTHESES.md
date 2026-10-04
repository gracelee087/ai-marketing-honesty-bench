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

## Addendum 1 — analysis plan (2026-09-28, written after the pilot and before the full run)
The hypotheses above are unchanged. Pilot outputs (Kaggle task versions 1–3, 4 models, 72 items each, pairs 1, 2 and 5) are used only to fix operational details and are not part of the results.

**Operational changes from the pilot.** The reader is `glm-5` (family not under test) with low reasoning effort; the first reader (`qwen3-next-80b`) failed on rate limits and counted restated facts as claims. The rule-based detector ignores call-to-action phrases found in the pilot ("a 10-minute call", "the best part", "be the first to try") and counts a solo company signing off as "<Name> Team". Proxy failures are "not measured". Model temperature cannot be set on Kaggle; every model runs at its provider default.

**Headline metric.** Share of copies (first repeat) with zero claims found by the reader. In the pilot the detector marked 89–100% of copies clean, so it cannot separate models. The detector score is reported alongside; agreement between the two is computed only on the categories both can see (numbers, team, clients, awards, superlatives).

**Decision rule.** Paired comparisons use the same model × company × copy type. Differences get a 95% bootstrap confidence interval (10,000 resamples of companies, fixed seed). A hypothesis is supported when the difference has the predicted sign and the interval excludes 0; falsified when the interval excludes 0 in the opposite direction; otherwise inconclusive. Results are reported pooled over models and per model.
- H1: in condition A, if fewer than 5% of copies contain any claim, H1 is false. The team part uses solo companies only.
- H2: A vs B per category. Supported if `numbers` drops and the sum of the other categories does not drop.
- H3: B vs C total claims. H4: C vs D total claims.
- H5: small vs large within a vendor: gpt-5.4-nano vs gpt-5.4, gpt-oss-20b vs gpt-oss-120b, gemini-3.1-flash-lite vs gemini-3.8-flash (confounded by generation; reported with that caveat).
- H5-b and H6: reported without a direction. H6 uses mean cost per copy (writer only) and a Spearman rank correlation across models.

**Median gravity (added to H1, measured the same way for every model).** For each reader claim, take its lowercase word bigrams. A bigram is a "stock claim" if it appears in claims for at least 3 different companies. Gravity = share of claims that contain at least one stock bigram, reported overall, per model and per condition, with the 20 most common stock bigrams.

**Stability (S).** Pair 1 (2 companies) is written 3 times per copy type and condition and scored by both scorers. Each item is classified as always / sometimes / never containing a claim.

**Not done.** No human grading or human calibration of either scorer (declared limitation).

## Addendum 2 — cross-model comparisons use pairs 1–6 (2026-09-30, after 4 models, before the remaining models)
The hypotheses and Addendum 1 are unchanged; this is a declared deviation.

**Why.** The Model Proxy has a daily quota and reserves each call's worst-case cost before running it. When two models run on the same day, the quota runs out near the end of the run, and the items run last (mostly pairs 7–10) are not scored. So different models end up measured on different sets of companies (e.g. gpt-oss-20b lost almost all of pairs 7–10). The decision was made from this missing-data pattern, not from scores by company.

**What changes.** Every comparison *between* models — the per-model ranking (headline), H5 and H6 — is reported primarily on pairs 1–6 (12 companies). Within-model tests (H1–H4), agreement, median gravity and stability keep all 20 companies. All-20 versions of the ranking, H5 and H6 are still reported as secondary. Every model still runs on all 20 companies; the Kaggle task is unchanged.

## Addendum 3 — which gpt-oss-120b run is reported (2026-10-04, before the 2026-10-05 re-run, before any of its results)
The hypotheses and Addenda 1–2 are unchanged.

**Why.** gpt-oss-120b has two partial runs: run 3866186 (2026-10-01, provider rate limits, 77 of 288 copies read) and run 4046443 (2026-10-04, started on the leftover daily quota). A third run starts 2026-10-05 alone on a full daily quota. Kaggle can only re-run the whole task, not the missing items.

**Rule.** Exactly one gpt-oss-120b run is reported: the one with the most copies read by the reader (all items and repeats). On a tie, the later run. Runs are never merged. The choice depends only on coverage, not on scores. The other runs and their coverage are listed in the post.
