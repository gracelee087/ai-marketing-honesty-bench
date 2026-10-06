# A selective-use instruction on new company briefs

This follow-up asks whether adding one sentence to the facts-only prompt changes fact-sheet copying without increasing reader-flagged unsupported claims. It uses ten new fictional company briefs, four selected writers and three conditions. Human evaluation is not part of the study.

The only addition from C to E is:

> Select the facts relevant to this audience; you do not need to include every field.

The added sentence does not mention copying, staffing, repetition or a required call to action. Conditions A and C retain the original email request and whitelist. Every brief contains a capability limitation, so this is a targeted stress test rather than a representative sample of marketing briefs.

## Results

All four planned writer runs completed on 2026-10-05: 120 generated emails and 109 valid reader judgments. Eleven reader responses reached the 8,192-token cap and returned empty content; these remain missing. No writer reached its token cap, no output was empty or shorter than twenty words, and 114/120 met the whitespace-based 100–150-word diagnostic. All 120 emails remain in the text analysis, including length violations.

| Condition | Reader-clean | Mean fact-sheet overlap | Solo emails saying no employees |
|---|---:|---:|---:|
| A: original request | 6/35 (17.1%) | 7.9% | 0/20 |
| C: facts only | 25/37 (67.6%) | 22.4% | 6/20 |
| E: C plus selection permission | 26/37 (70.3%) | 21.9% | 5/20 |

C increased mean overlap in every writer. The pooled paired C−A increase was 14.54 percentage points (95% company-bootstrap interval 12.55 to 16.38; forty pairs). The reader comparison remains descriptive under the locked coverage rule: GPT-5.4 had six matched A/C judgments and Gemini had seven, below the required eight per writer.

The predicted reduction from E was not established: E−C overlap was −0.55 percentage points (interval −1.97 to +0.89; forty pairs). Reader-clean change on the thirty-five matched C/E pairs was zero (interval −13.9 to +13.5 percentage points). The unmatched percentages in the table do not demonstrate improvement, and the paired interval does not establish equivalent factuality. These approximate intervals sample only ten companies and do not measure judge error.

Secondary paired changes: repetition increased 0.950 percentage points for C−A (interval 0.546 to 1.384), while E−C was +0.079 percentage points (−0.358 to +0.526). Staffing mentions increased 30 percentage points for C−A and fell 5 for E−C; these are descriptive results from only five solo-company briefs. All endpoints and model-level results are in the generated [report](out/report.md).

The reader passed 10/10 supported restatements, detected 10/10 wrong prices and detected 10/10 wrong team sizes. These are synthetic checks, not human calibration. Recorded writer-plus-reader usage including controls was **$2.2413678**. Kaggle reported **$2.9824297** of daily quota remaining at 2026-10-05 20:32:37 UTC after all jobs completed. No paid credits were purchased.

The [response manifest](out/response_manifest.json) records SHA-256 hashes of the five actual result files. [All forty C/E pairs](out/paired_examples.json) are retained; the inspection script's printed examples are chosen after seeing overlap changes, not prespecified case studies.

## Run and reproduce

- [Protocol](PROTOCOL.md), [new briefs](companies.json), and [frozen file hashes](freeze.json).
- [Main Kaggle task, version 2](https://www.kaggle.com/benchmarks/tasks/sohee087/marketing-facts-selective-validation/2).
- [Sonnet routing repair](https://www.kaggle.com/benchmarks/tasks/sohee087/marketing-facts-selective-validation-sonnet/1) and its [frozen source and reason](freeze_sonnet.json).
- [Synthetic reader controls](https://www.kaggle.com/benchmarks/tasks/sohee087/marketing-reader-synthetic-controls/1).

The saved responses are included. The commands below are offline and make no model calls. Run them from the repository root after installing `requirements-analysis.txt`:

The follow-up Kaggle task links above are provenance records for private tasks. Public reproduction uses the frozen source and saved responses included in this repository.

```bash
python validation_2026-10-05/analyze.py
python validation_2026-10-05/inspect_results.py
python validation_2026-10-05/figures.py
```

The analysis reads `downloads/**/results.jsonl`, verifies the frozen inputs, and produces `out/report.md`, condition and paired-contrast tables, raw paired examples and a figure. The planned denominator is 120 emails. Missing, malformed and unscored responses are reported explicitly. Do not interpret a platform registration-only zero as a writer result.

`manage.py` performs authenticated Kaggle operations only for these study tasks. Its launch receipts prevent automatic duplicate submission. Running its `launch` action uses quota; the offline commands above do not. The task runtime has observed-cost stops and does not buy credits or use another provider.

## What the controls establish

There are thirty known-construction controls: ten exact factual restatements, ten wrong-price injections and ten wrong-team-size injections. They use the same reader prompt, parser and reasoning setting as the email study. Passing these controls demonstrates behavior on those simple cases; it does not establish accuracy on all natural marketing prose or substitute for human validation.

## Registration and model routing

Kaggle executes a registration notebook using a default model. The initial task failed at registration without consuming quota. The corrected version skips calls for unplanned models; it records no study responses during registration. Separately, the Sonnet slug `claude-sonnet-5-default` appears inside the runtime as `anthropic/claude-sonnet-5@default`. Its first attempt also made zero study calls, so a separately frozen routing repair normalizes that spelling and schedules only Sonnet. The original model outputs from the other three writers are retained; no successful draft is regenerated or selected from alternatives.

The archived version-1 files match their original manifest hashes. Data, prompts, reader definitions and offline analysis remain the same across the routing repair. No human ratings or simulated writer outputs are included in the results.
