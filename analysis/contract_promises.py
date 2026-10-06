"""Post hoc phrase audit of saved outputs; no model calls or human labels.

Counts explicit contract/commitment claims, not a complete error rate.
The lexicon was chosen after looking at both studies on 2026-10-05.
"""
import collections
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results' / 'analysis' / 'contract_promises'
PATTERN = re.compile(
    r'\b(?:no|without(?:\s+any)?)\s+(?:long[\s\-\u2010-\u2015]+term\s+)?(?:contracts?|commitments?)\b'
    r'|\bcancel\s+(?:any\s*time|at\s+any\s+time)\b'
    r'|\bno\s+(?:(?:annual|long[\s\-\u2010-\u2015]+term)\s+)?lock[\s\-\u2010-\u2015]*in\b', re.I)


def read_records(path, digest):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]


def load():
    companies = {c['id']: c for c in json.loads((ROOT / 'data/companies.json').read_text(encoding='utf-8'))}
    manifest = json.loads((ROOT / 'results/manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        for row in read_records(ROOT / entry['file'], entry['sha256']):
            if row.get('repeat') == 0 and row.get('copy'):
                yield dict(row, study='original', model=entry['model'], facts=companies[row['company_id']]['facts'], source=entry['file'])
    directory = ROOT / 'validation_2026-10-05'
    companies = {c['id']: c for c in json.loads((directory / 'companies.json').read_text(encoding='utf-8'))}
    for entry in json.loads((directory / 'out/response_manifest.json').read_text(encoding='utf-8')):
        if '/writer/' not in entry['file']:
            continue
        path = directory / entry['file']
        for row in read_records(path, entry['sha256']):
            if row.get('copy'):
                yield dict(row, study='followup', model=path.parts[-3], copy_type='cold_email',
                           facts=companies[row['company_id']]['facts'], source=path.relative_to(ROOT).as_posix())


def main():
    # Saved copy includes Unicode punctuation that Windows' legacy pipe encoding
    # cannot represent. Keep redirected diagnostic output reproducible as UTF-8.
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    rows, evidence, summaries = [], [], collections.defaultdict(lambda: [0, 0])
    seen = set()
    for r in load():
        key = (r['study'], r['model'], r['company_id'], r['condition'], r['copy_type'])
        assert key not in seen
        seen.add(key)
        matches = list(PATTERN.finditer(r['copy']))
        phrases = [m.group() for m in matches]
        assert all(p in r['copy'] for p in phrases)
        item = {k: r[k] for k in ('study', 'model', 'company_id', 'condition', 'copy_type')}
        item.update(match=bool(matches), phrases=' | '.join(phrases), reader_scored=r.get('reader') is not None,
                    reader_clean=(r['reader']['total'] == 0) if r.get('reader') is not None else None, source=r['source'])
        rows.append(item)
        group = summaries[(r['study'], r['model'], r['condition'])]
        group[0] += 1
        group[1] += bool(matches)
        if matches:
            sentences = re.split(r'(?<=[.!?])\s+|\n+', r['copy'])
            evidence.append(dict(item, price=r['facts']['Price'], facts=r['facts'], copy=r['copy'],
                                 excerpts=[s for s in sentences if PATTERN.search(s)], reader=r.get('reader')))
    assert sum(r['study'] == 'original' for r in rows) == 2427
    assert sum(r['study'] == 'followup' for r in rows) == 120
    OUT.mkdir(exist_ok=True)
    with (OUT / 'all_items.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    table = [dict(study=k[0], model=k[1], condition=k[2], generated=v[0], matches=v[1]) for k, v in sorted(summaries.items())]
    with (OUT / 'by_model_condition.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    (OUT / 'matched_outputs.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (OUT / 'audit.json').write_text(json.dumps({
        'status': 'exploratory; lexicon chosen after reading both studies',
        'human_validation': False, 'model_calls': 0,
        'definition': PATTERN.pattern,
        'counts': dict(collections.Counter(r['study'] for r in rows)),
        'matches': dict(collections.Counter(r['study'] for r in evidence)),
        'scope': 'Explicit phrases only. Not all unsupported claims or all business terms. No causal claim about a prompt or general model ranking.',
    }, indent=2) + '\n', encoding='utf-8')
    case = {r['condition']: r for r in evidence if r['study'] == 'original' and r['model'] == 'claude-sonnet-5' and r['company_id'] == 'p02-team' and r['copy_type'] == 'cold_email'}
    assert set(case) == {'A_none', 'B_ban', 'C_whitelist', 'D_reinject'}
    selected = [r for r in evidence if r['study'] == 'followup' and r['model'] == 'claude-sonnet-5-default' and r['condition'] in ('C', 'E')]
    assert len(selected) == 7 and len({r['company_id'] for r in selected}) == 6
    for r in [*case.values(), *selected]:
        # Check the whole brief, not just the Price field.
        assert not re.search(r'contract|commitment|cancel|hidden\s+fee', ' '.join(r['facts'].values()), re.I)
        assert all(s in r['copy'] for s in r['excerpts'])
        assert r.get('reader') is not None
        assert any(PATTERN.search(c['quote']) for c in r['reader']['claims'])
    report = [
        '# The price was copied correctly and the contract terms were added\n\n',
        'Exploratory finding from saved responses, 2026-10-05. No new model calls or human ratings. The phrase lexicon and this case selection were made after inspecting both studies; this is not a new preregistered result.\n\n',
        '## One company across all four instructions\n\n',
        'Backhaul Board is a fictional freight-listing service. Its complete seven-field brief specifies **$79 per truck per month** and says nothing about contract length, cancellation, or hidden fees. The saved Sonnet 5 cold emails contain:\n\n',
        '| Condition | Exact generated sentence |\n|---|---|\n',
    ]
    labels = {'A_none': 'A: original request', 'B_ban': 'B: do not invent numbers', 'C_whitelist': 'C: use only the supplied facts', 'D_reinject': 'D: C plus repeated facts'}
    for condition, label in labels.items():
        report.append(f"| {label} | {case[condition]['excerpts'][0]} |\n")
    report.extend([
        '\nThe numerical price and billing unit are preserved in all four sentences. Contract freedom is an additional assertion. In C and D it also conflicts with the instruction not to add unlisted claims. The issue can be seen by comparing the brief and the sentence; it does not depend on whether a reviewer likes the writing.\n\n',
        '**The original glm-5 reader caught the contract claim in all four cases.** This is a writer failure, not a newly discovered reader blind spot. It does not show that a real contract was changed or that a customer saw the draft.\n\n',
        '## The same phrase pattern in the ten-company follow-up\n\n',
        'Every follow-up brief specifies a paid price. None supplies contract duration or cancellation terms. Counts below use all generated emails, including any with missing reader judgments. Each cell has ten emails.\n\n',
        '| Writer | A | C | E |\n|---|---:|---:|---:|\n',
    ])
    for model in sorted({r['model'] for r in rows if r['study'] == 'followup'}):
        vals = [summaries[('followup', model, condition)] for condition in ('A', 'C', 'E')]
        report.append('| ' + model + ' | ' + ' | '.join(f'{v[1]}/{v[0]}' for v in vals) + ' |\n')
    report.extend([
        '\nSonnet has seven matches among its twenty C/E emails, spanning six companies. All seven promise no contracts or no long-term commitment, and all seven were flagged for that claim by the original reader. The source briefs contain no corresponding policy. This subtype was identified after seeing the follow-up too, so the counts are a second observed dataset, not a prospective validation of this specific hypothesis.\n\n',
        'The 2/10 versus 5/10 counts do not establish that E makes the issue worse. A zero for another writer means no match for this narrow phrase list, not no invented commercial terms.\n\n',
        '## Exact follow-up examples\n\n| Company | Condition | Supplied price | Exact generated sentence |\n|---|---|---|---|\n',
    ])
    for r in sorted(selected, key=lambda r: (r['company_id'], r['condition'])):
        report.append(f"| {r['facts']['Company']} | {r['condition']} | {r['price']} | {r['excerpts'][0]} |\n")
    report.extend([
        '\n## Scope and reproduction\n\n',
        'The broader scan also matches legitimate or ambiguous language about free browsing and no-obligation demos. Its total match count must not be reported as an error count. Full copies, complete briefs, original reader claims and source paths are preserved for every match in [matched_outputs.json](matched_outputs.json); [all_items.csv](all_items.csv) includes all 2,547 generated first-repeat original/follow-up items and zero matches too.\n\n',
        'Run `python analysis/contract_promises.py` from the repository root. It verifies input hashes against the saved manifests, checks exact quote provenance, and regenerates this report. Original hypotheses, reader results and frozen follow-up inputs are unchanged.\n\n',
        'The concrete question this finding motivates is whether the model treats an unspecified commercial policy as an absent requirement. Testing that explanation or a policy-specific prompt repair would require a newly frozen experiment. Neither has been tested here.\n',
    ])
    (OUT / 'report.md').write_text(''.join(report), encoding='utf-8')
    print('Summary (phrase counts, not independently validated error rates):')
    for item in table:
        if item['study'] == 'followup' or item['matches']:
            print(json.dumps(item))
    print('Every matched output:')
    for r in evidence:
        print(json.dumps({k: r[k] for k in ('study', 'model', 'company_id', 'condition', 'copy_type', 'price', 'excerpts', 'reader_scored', 'reader_clean')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
