# New-company follow-up results

Frozen: 2026-10-05T19:54:28.805420+00:00. No human evaluation.

Ten fictional company briefs, four selected writers, one email each under A / C / E. E adds only permission to select relevant facts. Text figures use generated copies; reader figures exclude invalid/missing judgments.

## Conditions

| condition | planned | recorded | generated | read | clean_n | clean_share | mean_overlap | mean_repeat_share | solo_generated | says_no_employees | cost_usd |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 40 | 40 | 40 | 35 | 6 | 0.1714 | 0.0790 | 0.0007 | 20 | 0 | 0.8261 |
| C | 40 | 40 | 40 | 37 | 25 | 0.6757 | 0.2244 | 0.0102 | 20 | 6 | 0.6277 |
| E | 40 | 40 | 40 | 37 | 26 | 0.7027 | 0.2189 | 0.0110 | 20 | 5 | 0.6529 |

## Paired changes

| contrast | measure | n_pairs | companies | difference | lo | hi | coverage |
|---|---|---|---|---|---|---|---|
| C-A | clean | 32 | 10 | 0.4375 | 0.2500 | 0.6216 | descriptive |
| C-A | claims | 32 | 10 | -1.3438 | -2.0938 | -0.8286 | descriptive |
| C-A | overlap | 40 | 10 | 0.1454 | 0.1255 | 0.1638 | complete-enough |
| C-A | repeat_share | 40 | 10 | 0.0095 | 0.0055 | 0.0138 | complete-enough |
| C-A | no_employees | 20 | 5 | 0.3000 | 0.2500 | 0.4000 | descriptive |
| E-C | clean | 35 | 10 | 0.0000 | -0.1389 | 0.1351 | complete-enough |
| E-C | claims | 35 | 10 | 0.1714 | -0.1765 | 0.5556 | complete-enough |
| E-C | overlap | 40 | 10 | -0.0055 | -0.0197 | 0.0089 | complete-enough |
| E-C | repeat_share | 40 | 10 | 0.0008 | -0.0036 | 0.0053 | complete-enough |
| E-C | no_employees | 20 | 5 | -0.0500 | -0.1500 | 0.0000 | descriptive |

Changes are B minus A as named in each contrast. Intervals resample ten companies 10,000 times; small-sample and judge uncertainty remain. No interval establishes marketing usability. Staffing has five companies and is secondary.

## By model

| model | condition | recorded | generated | read | clean_share | mean_overlap | mean_repeat_share | cost_usd |
|---|---|---|---|---|---|---|---|---|
| claude-sonnet-5-default | A | 10 | 10 | 10 | 0.0000 | 0.0581 | 0.0014 | 0.2079 |
| claude-sonnet-5-default | C | 10 | 10 | 9 | 0.1111 | 0.1055 | 0.0007 | 0.1942 |
| claude-sonnet-5-default | E | 10 | 10 | 9 | 0.1111 | 0.0845 | 0.0000 | 0.2116 |
| gemini-3.8-flash | A | 10 | 10 | 7 | 0.1429 | 0.0549 | 0.0000 | 0.2344 |
| gemini-3.8-flash | C | 10 | 10 | 10 | 1.0000 | 0.3779 | 0.0353 | 0.1337 |
| gemini-3.8-flash | E | 10 | 10 | 10 | 1.0000 | 0.3972 | 0.0384 | 0.1380 |
| gpt-5.4-2026-03-05 | A | 10 | 10 | 8 | 0.3750 | 0.1008 | 0.0016 | 0.2166 |
| gpt-5.4-2026-03-05 | C | 10 | 10 | 8 | 0.8750 | 0.2158 | 0.0033 | 0.1949 |
| gpt-5.4-2026-03-05 | E | 10 | 10 | 9 | 0.8889 | 0.1928 | 0.0039 | 0.1650 |
| gpt-5.4-nano-2026-03-17 | A | 10 | 10 | 10 | 0.2000 | 0.1024 | 0.0000 | 0.1671 |
| gpt-5.4-nano-2026-03-17 | C | 10 | 10 | 10 | 0.7000 | 0.1984 | 0.0016 | 0.1048 |
| gpt-5.4-nano-2026-03-17 | E | 10 | 10 | 9 | 0.7778 | 0.2011 | 0.0019 | 0.1384 |

## Status and missingness

| model | status | n |
|---|---|---|
| claude-sonnet-5-default | invalid_reader | 2 |
| claude-sonnet-5-default | scored | 28 |
| gemini-3.8-flash | invalid_reader | 3 |
| gemini-3.8-flash | scored | 27 |
| gpt-5.4-2026-03-05 | invalid_reader | 5 |
| gpt-5.4-2026-03-05 | scored | 25 |
| gpt-5.4-nano-2026-03-17 | invalid_reader | 1 |
| gpt-5.4-nano-2026-03-17 | scored | 29 |

Writer cap reached: 0; reader cap reached: 11.

## Synthetic reader controls

| kind | recorded | scored | passed |
|---|---|---|---|
| supported | 10 | 10 | 10 |
| wrong_price | 10 | 10 | 10 |
| wrong_team | 10 | 10 | 10 |

These known-construction controls test obvious restatements and injected numeric claims. They are not human calibration or an accuracy estimate on natural marketing prose.
