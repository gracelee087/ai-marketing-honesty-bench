# Analysis corrections — 2026-10-05

These are corrections and exploratory reporting choices made after observing the saved version-4 results. They do not alter the original hypotheses, the version-4 task, saved writer responses, or reader scores. No additional model calls were made.

## Reader scores and wording

The article says “reader-clean” or “checker found no unsupported claim.” It does not equate this with proven truth. Reader categories such as `numbers` can include vague quantities and disputed inferences; neither the broad `hard_claim` bucket nor the digit-filtered `concrete` diagnostic is a human-verified count of fabricated customers or numbers. They remain exploratory diagnostics in the full report.

## Invitation rules

An early rule treated many explicit invitations as absent. A later broad rule could count product nouns such as “meeting” as a request. `analysis/invitations.py`, version `invitation-cues-2`, searches for explicit request/offer patterns in the body, excluding subject lines. A conversation label additionally requires a conversation term in that sentence. The audit exports the matched sentence and cue.

Absence means **no recognized cue**, not proven absence of a call to action. Both false positives and false negatives remain possible. The regression tests cover known misses and product-description counterexamples; they do not estimate accuracy on held-out human labels. Previous “no ask” percentages must not be reused. Invitation statistics are excluded from the main article's aggregate findings.

## Text measures in the article

- Fact overlap: tokenize using `extra.WORD`, lowercase, then count words covered by an exact four-token window also present in the concatenated fact-sheet values. Punctuation and case are ignored. Legitimate technical language also counts.
- Repetition: `(number of four-token windows − number of distinct windows) / number of windows`. The 5% illustration is exploratory.
- Staffing: match the `NO_EMPLOYEES` expressions in `extra.py`. The prompt comparison uses all generated first-repeat texts for solo-founder companies, including texts without a reader score.
- Gemini illustration: all 60 generated and scored first-repeat outputs from gemini-3.8-flash in condition C, all 20 companies and three formats. Three checks require overlap below 50%, repetition below 5%, and no staffing match. Invitations are excluded. This is not a quality score or a new model ranking.

## Reproduction and provenance

`analysis/export_results.py` creates the portable bundle from locally selected runs, with allowlisted fields and no provider error text. `analysis/reproduce.py` reads the bundle without importing the live benchmark or making model calls. The manifest freezes task source, fact sheets, hypotheses and exported results. `validate_submission.py` checks record identities, scorer arithmetic, article numerators, quote provenance, and agreement between original and portable analyses when original runs are present.

Earlier review scripts and draft snapshots under `review_2026-10-05` are historical working material; the supported reproduction entry point is `analysis/reproduce.py`.

## Exploratory contract phrases — 2026-10-05

`analysis/contract_promises.py` searches saved first-repeat original outputs and all 120 follow-up emails for explicit no-contract/no-commitment/cancel-anytime/no-lock-in phrases. Both datasets had been inspected before choosing this lexicon and the illustrative company. This is post hoc analysis, with no new model calls or human labels. It does not change original scores, hypotheses or frozen follow-up inputs.

The generated report separates a specific exact-price/unlisted-contract example from broad phrase counts. Broad matches include free browsing and no-obligation demos, so their total is not an error rate. The seven selected Sonnet C/E follow-up examples have complete source briefs without corresponding terms, exact saved quotes, and existing reader flags for the contract claim. This is a writer-error illustration, not a claim that the reader missed it. The 2/10 versus 5/10 counts are descriptive and do not establish that the selective-use instruction worsens this subtype.

The report, every matched full output, and all generated item denominators are retained under `results/analysis/contract_promises`. The script verifies saved-response hashes and checks the selected quotations and their source fields before writing the report. This new subtype has not yet received a prospectively specified validation experiment.

## Saved-data and inference audit — 2026-10-06

A second audit compared the original saved JSONL records with the portable bundle, checked the embedded task briefs against `data/companies.json`, reconstructed item grids and recomputed the primary and follow-up paired estimates without importing their production analysis functions. All 19 reproduced original CSV tables matched the saved tables before corrections. The original 2,898 generated / 2,665 scored texts and 2,208 scored first-repeat texts, and the follow-up 120 generated / 109 scored emails, remain unchanged. The selected run is the highest-coverage run among locally retained candidates for every model. Older attempts without saved response files cannot be audited in full.

Two inference corrections were made after this audit, without editing hypotheses, task source, saved outputs, scores or frozen follow-up inputs:

- H2 previously treated an uncertain non-number decrease as evidence of no decrease. Sonnet 5 had a number-claim decrease but an other-claim interval of −0.722 to +0.194. Its joint H2 label is now **inconclusive**, previously **supported**. With no prespecified equivalence margin, an interval spanning zero cannot establish that other claims stayed the same. Support now requires a clear numeric decrease and a clear other-claim increase; a clear decrease in other claims contradicts H2.
- gpt-oss-120b's H2 comparison has only one matched item from one company. Resampling that company previously produced an artificial zero-width interval and a **falsified** label. The mean remains descriptive; its interval is now unavailable and its label **inconclusive**. Company counts are included in H2–H4 tables. Its separate H4 comparison has only four companies and remains fragile; no new arbitrary sample threshold was added.

The pooled H2 contradiction, H3 support, H4 uncertainty, H5 results, article numerators and headline model rates are unchanged. Regression tests cover the invalid no-effect inference, joint directional evidence, a single cluster and empty data.

Additional post hoc sensitivity checks:

- Restricting ten sufficiently covered models to the same 110 scored items gives GPT-5.4 and Gemini 3.8 Flash 83/110 each (75.5%). Comparing those two alone on their 142 shared scored items gives a +4.93-point reader-clean difference for GPT-5.4 (95% company-bootstrap interval −4.17 to +13.89 points). The available-item ranking does not establish a clear winner.
- Forty-five original reader claim quotes in 37 scored outputs are not exact substrings of their generated copy; 26 outputs belong to the first-repeat analysis. These include formatting differences and paraphrases and are **not** 45 proven scoring errors. Version 4 did not validate exact quote substrings; the follow-up does. Original scores are retained. Excluding the 26 entire judgments as a sensitivity check leaves 2,182 scores, with clean shares A 105/543, B 205/542, C 371/546 and D 393/551. Paired differences remain negative for B−A numbers (−0.192, interval −0.255 to −0.130), B−A other claims (−0.605, −0.832 to −0.403) and C−B total claims (−0.769, −0.952 to −0.619); D−C remains inconclusive (−0.094, −0.242 to +0.047). This diagnostic does not validate judge accuracy.
- Clustering the original prompt contrasts by the ten company pairs instead of twenty individual companies leaves the same pooled H2–H4 conclusions. Removing any one writer leaves the direction of each pooled point estimate unchanged; that direction-only check is not an additional significance claim.

Windows reproduction also exposed a console-encoding failure while the follow-up inspection script printed an example. Its output stream now uses UTF-8. This affects display only; the frozen analysis and response data are unchanged.
