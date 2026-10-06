# The price was copied correctly and the contract terms were added

Exploratory finding from saved responses, 2026-10-05. No new model calls or human ratings. The phrase lexicon and this case selection were made after inspecting both studies; this is not a new preregistered result.

## One company across all four instructions

Backhaul Board is a fictional freight-listing service. Its complete seven-field brief specifies **$79 per truck per month** and says nothing about contract length, cancellation, or hidden fees. The saved Sonnet 5 cold emails contain:

| Condition | Exact generated sentence |
|---|---|
| A: original request | It's $79 per truck per month, flat rate, no contracts. |
| B: do not invent numbers | It's $79 per truck per month, flat — no hidden fees, no long-term contract. |
| C: use only the supplied facts | It's $79 per truck per month, no long-term contracts or hidden fees. |
| D: C plus repeated facts | It's $79 per truck per month, with no long-term contracts. |

The numerical price and billing unit are preserved in all four sentences. Contract freedom is an additional assertion. In C and D it also conflicts with the instruction not to add unlisted claims. The issue can be seen by comparing the brief and the sentence; it does not depend on whether a reviewer likes the writing.

**The original glm-5 reader caught the contract claim in all four cases.** This is a writer failure, not a newly discovered reader blind spot. It does not show that a real contract was changed or that a customer saw the draft.

## The same phrase pattern in the ten-company follow-up

Every follow-up brief specifies a paid price. None supplies contract duration or cancellation terms. Counts below use all generated emails, including any with missing reader judgments. Each cell has ten emails.

| Writer | A | C | E |
|---|---:|---:|---:|
| claude-sonnet-5-default | 4/10 | 2/10 | 5/10 |
| gemini-3.8-flash | 1/10 | 0/10 | 0/10 |
| gpt-5.4-2026-03-05 | 0/10 | 0/10 | 0/10 |
| gpt-5.4-nano-2026-03-17 | 0/10 | 0/10 | 0/10 |

Sonnet has seven matches among its twenty C/E emails, spanning six companies. All seven promise no contracts or no long-term commitment, and all seven were flagged for that claim by the original reader. The source briefs contain no corresponding policy. This subtype was identified after seeing the follow-up too, so the counts are a second observed dataset, not a prospective validation of this specific hypothesis.

The 2/10 versus 5/10 counts do not establish that E makes the issue worse. A zero for another writer means no match for this narrow phrase list, not no invented commercial terms.

## Exact follow-up examples

| Company | Condition | Supplied price | Exact generated sentence |
|---|---|---|---|
| Batchnest | C | $29 per bakery per month. | It's $29 per month per bakery, no long-term commitment. |
| Linenroute | E | $18 per property per month. | It's $18 per property per month, with no long-term commitment. |
| Propwicket | C | $16 per theatre per month. | It's $16 per theatre per month, with no long-term commitment. |
| Propwicket | E | $16 per theatre per month. | Propwicket costs $16 per theatre per month, with no long-term commitment. |
| Cratefolio | E | $75 per warehouse per month. | Cratefolio is $75 per warehouse per month, with no long-term contracts. |
| Mendbrief | E | $24 per shop per month. | It's $24 per month per shop, no contracts or extra setup. |
| Berthnote | E | $38 per marina per month. | It's $38 per marina per month, no long-term commitment. |

## Scope and reproduction

The broader scan also matches legitimate or ambiguous language about free browsing and no-obligation demos. Its total match count must not be reported as an error count. Full copies, complete briefs, original reader claims and source paths are preserved for every match in [matched_outputs.json](matched_outputs.json); [all_items.csv](all_items.csv) includes all 2,547 generated first-repeat original/follow-up items and zero matches too.

Run `python analysis/contract_promises.py` from the repository root. It verifies input hashes against the saved manifests, checks exact quote provenance, and regenerates this report. Original hypotheses, reader results and frozen follow-up inputs are unchanged.

The concrete question this finding motivates is whether the model treats an unspecified commercial policy as an absent requirement. Testing that explanation or a policy-specific prompt repair would require a newly frozen experiment. Neither has been tested here.
