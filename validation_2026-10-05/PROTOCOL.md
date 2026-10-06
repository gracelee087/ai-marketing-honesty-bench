# Held-out marketing validation

This follow-up tests whether the version-4 exploratory findings recur on ten new fictional company briefs. It also tests a selective-use instruction. The original study and its hypotheses stay unchanged. This protocol, data, task source, scorer and analysis source are frozen with SHA-256 hashes before the first writer call. Local freezing is not an independently timestamped preregistration.

## Scope and predictions

Four deliberately selected writers: `gpt-5.4-2026-03-05`, `gpt-5.4-nano-2026-03-17`, `gemini-3.8-flash`, and `claude-sonnet-5-default`. They span the original reader-score and copying patterns. This is a targeted follow-up, not a representative model sample or a new leaderboard.

Ten new company briefs, five solo and five small teams. One cold email per company, writer and condition: 120 planned outputs. There are no retries for successful outputs and no selection among alternative drafts. Each prompt asks for 100–150 words including a subject line, as in the original study. There is no human evaluation.

Conditions:

- A: fact sheet plus the original cold-email request.
- C: A plus the original whitelist: `Use only the facts above. Do not add numbers, clients, team members, awards, or claims that are not listed.`
- E: C plus `Select the facts relevant to this audience; you do not need to include every field.`

E deliberately keeps C's factual restriction and adds only selective-use permission. It does not explicitly ban copying, mention employees, or mandate a CTA. This isolates whether selection permission changes the measured behavior. Every new brief includes a capability limitation; this is a targeted stress test of selective use, not a representative marketing sample.

Confirmatory follow-up contrasts, stated before these outputs:

1. C versus A: reader-clean share increases; fact-sheet overlap increases. Staffing mentions and repetition are secondary replication endpoints.
2. E versus C: fact-sheet overlap decreases. Reader-clean change is reported alongside it; a non-significant decline is not evidence of equivalent factuality. No marketing-quality or conversion claim is tested.

The primary population is all ten companies and four selected models. Staffing uses the five solo companies. Per-model results are descriptive given ten companies per condition. Human usability and factuality verification are explicitly outside scope.

## Measurement

The reader is `glm-5`, using the original six-category prompt and `reasoning="low"`. It sees the fact sheet and output, not the writer identity or condition. The saved raw reader response is retained. Parser validation requires a list of known-category claims with nonempty exact-substring quotes; invalid responses are missing, never clean. An empty list is valid. This hardens parsing relative to version 4 without changing the reader instructions. No claim is automatically discarded merely because it seems questionable.

Text measures reproduce the prior definitions: lowercase four-token fact overlap; proportion of duplicate four-token windows; fixed no-employees phrase variants. Copies include subject and sign-off. Empty or non-prose outputs are reported separately. Word count and limit compliance are diagnostics. No invitation regex or combined quality score is a primary outcome.

Prompt contrasts pair on writer and company. Resample companies 10,000 times with seed 20261005, retaining all models in each sampled company. Report paired means and percentile 95% bootstrap intervals; with only ten companies these intervals are approximate. All endpoints and contrasts are reported, including null or reversed findings. There is no multiple-comparison-adjusted discovery claim. Full-case and available-pair counts are explicit. A confirmatory label requires at least eight matched companies per writer and thirty matched writer-company pairs overall; otherwise report incomplete descriptive results.

## Synthetic reader controls

Thirty deterministic controls, three per company: (i) copy exact product/price facts, with no added claim; (ii) add an explicit monthly/annual price of $987 while retaining the original brief; (iii) assert a team of 97 employees. Correct baseline controls have an empty claim list; injected controls require a flag whose quote covers the altered price/staff statement. Report control clean specificity and injection detection separately, with every error visible. These are obvious synthetic checks and do not establish accuracy on natural, ambiguous marketing prose.

The control task uses the same reader prompt, low reasoning setting and parser. It runs once, not separately for each writer. Its results cannot be called human labels or human validation. If controls expose failures, report them without rewriting the locked reader or silently removing outputs.

## Execution and missingness

All conditions for a company are consecutive, with their order shuffled using seed 20261005; company order is shuffled too. The same schedule is used across models. New isolated chat per writer/reader call. Provider defaults remain except fixed writer output caps: OpenAI 4096 completion tokens, Anthropic 4096 tokens, Google 4096 output tokens. Reader cap is 8192 tokens with low reasoning. Caps are constant within each writer and all three conditions; capped follow-up results are not pooled with the original default-cap study.

At most two items execute concurrently in each task. Transient 429/overload responses get at most three attempts with 5/10-second backoff. Quota and authentication failures are not retried. Completed outputs are never regenerated. Failed writer calls and reader calls remain explicit; numeric usage and any cap-hit indicator are reported.

Use existing Kaggle free quota only. The observed pre-run remaining quota was $5.2237975. Estimated ordinary usage is below $3, not a guaranteed charge. Each writer run stops starting new items after $0.80 of observed writer+reader usage; the controls have a $0.40 observed-use stop. Calls already in flight can exceed a stop slightly. Do not buy credits or switch providers. If the quota prevents completion, retain and report the incomplete run rather than rerunning to select a better result.

## Reporting

The follow-up report includes frozen hashes, UTC freeze time, Kaggle task/version/run identifiers, every planned item status, actual coverage/cost, synthetic controls, all prompt contrasts and example outputs. Every sampled email is retained, not only examples supporting the story. The submission changes only after actual results are available. Any post-freeze implementation correction gets a dated deviation and a new version; no unnoticed replacement of the frozen files.

## Registration correction before the planned model runs

2026-10-05: writer task version 1 failed during Kaggle task registration with no valid reader results. No scheduled model runs existed and quota remained $4.7762025 used out of $10. The registration notebook uses a platform-selected model. Version 2 skips calls for models outside the four preselected writers (or outside glm-5 for controls); its registration-only placeholder is never an experimental score. Google caps use `max_tokens=4096` through Kaggle's OpenAI-compatible adapter, rather than the incompatible native `max_output_tokens` keyword. The intended token ceiling, prompts, data, reader and analysis are unchanged. The original uploaded source and manifest are preserved under `history/registration_v1`; a new freeze precedes all planned model runs.
