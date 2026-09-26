"""All-block descriptive contrasts. No empirical PASS or population inference."""
from __future__ import annotations
import argparse
import csv
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import statistics

DATA_SHA256 = '8cd29d3eeb50db949f174dafe2c1a62602df103e6eca4630478c402dadb6d093'
MODES = ('single_whole', 'single_chunked', 'batch_whole', 'batch_chunked')
FIELDS = ('block', 'load', 'mode', 'case_id', 'samples', 'received',
          'fresh_completions', 'median_age_twice_ns', 'cues',
          'source_cues', 'current_delivery_cues', 'bad_cues')

def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)

def validate(rows: list[dict]) -> dict[tuple, dict]:
    require(len(rows) == 32, '32 cases required')
    keyed = {}
    for row in rows:
        require(set(row) == set(FIELDS), 'column schema')
        for field in set(FIELDS) - {'load', 'mode', 'case_id'}:
            require(type(row[field]) is int and row[field] >= 0, 'integer:' + field)
        b, load, mode = row['block'], row['load'], row['mode']
        require(b in range(4) and load in ('idle', 'busy') and mode in MODES, 'factor identity')
        require(row['case_id'] == f'b{b:02d}-{load}-{mode}', 'case identity')
        key = (b, load, mode)
        require(key not in keyed, 'duplicate case')
        require(0 <= row['fresh_completions'] <= row['received'] <= row['samples']
                and row['samples'] > 0 and row['received'] > 0, 'count bounds')
        require(row['median_age_twice_ns'] > 0, 'positive median required')
        require(row['cues'] == 12 and row['current_delivery_cues'] <= row['source_cues'] <= 12
                and row['bad_cues'] <= 12, 'cue bounds')
        keyed[key] = row
    expected = {(b, load, mode) for b in range(4) for load in ('idle', 'busy') for mode in MODES}
    require(set(keyed) == expected, 'factorial completeness')
    return keyed

def load_table(path: Path, expected_digest: str = DATA_SHA256) -> list[dict]:
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == expected_digest, 'table digest')
    reader = csv.DictReader(io.StringIO(data.decode('utf-8')))
    require(reader.fieldnames == list(FIELDS), 'column order')
    rows = []
    for row in reader:
        for key in set(FIELDS) - {'load', 'mode', 'case_id'}:
            text = row[key]
            require(type(text) is str and text.isascii() and text.isdecimal(), 'CSV integer syntax')
            row[key] = int(text)
        rows.append(row)
    validate(rows)
    return rows

def summarize(values: list[Fraction], scale: int = 1) -> dict:
    scaled = [v * scale for v in values]
    return {'per_block': [float(v) for v in scaled],
            'exact_per_block': [str(v) for v in scaled],
            'median': float(statistics.median(scaled)),
            'min': float(min(scaled)), 'max': float(max(scaled)), 'n_blocks': len(values)}

def analyze(rows: list[dict]) -> dict:
    keyed = validate(rows)
    result = {'analysis': 'POSTHOC_DESCRIPTIVE_ONLY',
              'empirical_decision': 'HOLD_CUE_INTEGRITY',
              'model_task_acceptance': 'UNMEASURED',
              'case_count': len(rows), 'cases_excluded': 0,
              'cue_violations': sum(r['bad_cues'] for r in rows),
              'captures': sum(r['samples'] for r in rows),
              'received': sum(r['received'] for r in rows), 'strata': {}}
    pairs = {'batch_at_whole': ('single_whole', 'batch_whole'),
             'batch_at_chunked': ('single_chunked', 'batch_chunked'),
             'chunk_at_single': ('single_whole', 'single_chunked'),
             'chunk_at_batch': ('batch_whole', 'batch_chunked'),
             'combined': ('single_whole', 'batch_chunked')}
    for load in ('idle', 'busy'):
        cell = {}
        coverage = {}
        for mode in MODES:
            selected = [keyed[b, load, mode] for b in range(4)]
            coverage[mode] = [Fraction(r['fresh_completions'], r['samples']) for r in selected]
            cell[mode] = {'samples': sum(r['samples'] for r in selected),
                          'received': sum(r['received'] for r in selected),
                          'fresh_completions': sum(r['fresh_completions'] for r in selected),
                          'current_delivery_cues': sum(r['current_delivery_cues'] for r in selected),
                          'source_cues': sum(r['source_cues'] for r in selected),
                          'cue_violations': sum(r['bad_cues'] for r in selected)}
        contrasts = {}
        differences = {}
        for name, (reference, candidate) in pairs.items():
            diffs, age_ratios, cue_diffs = [], [], []
            for b in range(4):
                before, after = keyed[b, load, reference], keyed[b, load, candidate]
                diffs.append(coverage[candidate][b] - coverage[reference][b])
                age_ratios.append(Fraction(after['median_age_twice_ns'], before['median_age_twice_ns']))
                cue_diffs.append(Fraction(after['current_delivery_cues'] - before['current_delivery_cues'], 12))
            differences[name] = diffs
            contrasts[name] = {'completion_coverage_delta_pp': summarize(diffs, 100),
                               'median_age_ratio_candidate_over_reference': summarize(age_ratios),
                               'current_delivery_cue_delta_pp': summarize(cue_diffs, 100)}
        interaction = [differences['batch_at_chunked'][b] - differences['batch_at_whole'][b] for b in range(4)]
        for b in range(4):
            require(interaction[b] == differences['chunk_at_batch'][b] - differences['chunk_at_single'][b], 'interaction identity')
            require(differences['combined'][b] == differences['batch_at_whole'][b] + differences['chunk_at_batch'][b], 'path identity A')
            require(differences['combined'][b] == differences['chunk_at_single'][b] + differences['batch_at_chunked'][b], 'path identity B')
        result['strata'][load] = dict(cells=cell, contrasts=contrasts,
                                     coverage_interaction_pp=summarize(interaction, 100),
                                     exact_decomposition_checks=12)
    return result

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, default=Path(__file__).with_name('cases.csv'))
    parser.add_argument('--out', type=Path, help='exclusive new output file; default stdout')
    args = parser.parse_args()
    result = analyze(load_table(args.cases))
    text = json.dumps(result, sort_keys=True, indent=2) + '\n'
    if args.out:
        with args.out.open('x', encoding='utf-8') as stream:
            stream.write(text)
    else:
        print(text, end='')

if __name__ == '__main__':
    main()
