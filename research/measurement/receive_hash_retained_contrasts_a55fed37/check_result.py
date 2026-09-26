"""Independent Decimal/matrix reconstruction; imports neither analysis module."""
import argparse
import csv
from decimal import Decimal, localcontext
import json
from pathlib import Path


def check(cases: Path, output: Path) -> dict:
    errors = []
    def need(condition, message):
        if not condition:
            errors.append(message)
    with cases.open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    result = json.loads(output.read_text())
    modes = ['single_whole', 'single_chunked', 'batch_whole', 'batch_chunked']
    need(len(rows) == 32, 'case count')
    matrix = [(-1, 0, 1, 0), (0, -1, 0, 1), (-1, 1, 0, 0), (0, 0, -1, 1), (-1, 0, 0, 1)]
    names = ['batch_at_whole', 'batch_at_chunked', 'chunk_at_single', 'chunk_at_batch', 'combined']
    endpoints = [(0, 2), (1, 3), (0, 1), (2, 3), (0, 3)]
    lookup = {(int(r['block']), r['load'], r['mode']): r for r in rows}
    need(len(lookup) == 32, 'duplicate identity')
    need(result['empirical_decision'] == 'HOLD_CUE_INTEGRITY', 'retained HOLD')
    need(result['analysis'] == 'POSTHOC_DESCRIPTIVE_ONLY', 'analysis scope')
    need(result['case_count'] == 32 and result['cases_excluded'] == 0, 'complete retention')
    for key, field in [('captures', 'samples'), ('received', 'received'), ('cue_violations', 'bad_cues')]:
        need(type(result[key]) is int and result[key] == sum(int(r[field]) for r in rows), key)
    comparisons = 0
    def compare_summary(actual, values, label):
        nonlocal comparisons
        ordered = sorted(values)
        expected = dict(per_block=values, median=(ordered[1] + ordered[2]) / 2,
                        min=ordered[0], max=ordered[-1])
        need(type(actual['n_blocks']) is int and actual['n_blocks'] == 4, label + ':n')
        need(len(actual['per_block']) == len(actual['exact_per_block']) == 4, label + ':length')
        def equal(a, b, tag):
            nonlocal comparisons
            comparisons += 1
            need(type(a) in (int, float) and abs(Decimal(str(a)) - b) <= Decimal('1e-12'), tag)
        for i in range(4):
            equal(actual['per_block'][i], values[i], label + ':block')
            text = actual['exact_per_block'][i].split('/')
            exact = Decimal(text[0]) / (Decimal(text[1]) if len(text) == 2 else 1)
            need(abs(exact - values[i]) <= Decimal('1e-40'), label + ':rational')
        for name in ['median', 'min', 'max']:
            equal(actual[name], expected[name], label + ':' + name)
    with localcontext() as ctx:
        ctx.prec = 60
        for load in ['idle', 'busy']:
            strata = result['strata'][load]
            rates, times, cues = [], [], []
            for b in range(4):
                selected = [lookup[b, load, mode] for mode in modes]
                rates.append([Decimal(r['fresh_completions']) / Decimal(r['samples']) for r in selected])
                times.append([Decimal(r['median_age_twice_ns']) for r in selected])
                cues.append([Decimal(r['current_delivery_cues']) / 12 for r in selected])
            for name, coefficients, (before, after) in zip(names, matrix, endpoints):
                record = strata['contrasts'][name]
                rate_delta = [100 * sum(c * q for c, q in zip(coefficients, r)) for r in rates]
                ratio = [t[after] / t[before] for t in times]
                cue_delta = [100 * sum(c * q for c, q in zip(coefficients, r)) for r in cues]
                compare_summary(record['completion_coverage_delta_pp'], rate_delta, load + ':' + name + ':coverage')
                compare_summary(record['median_age_ratio_candidate_over_reference'], ratio, load + ':' + name + ':age')
                compare_summary(record['current_delivery_cue_delta_pp'], cue_delta, load + ':' + name + ':cue')
            interaction = [100 * (r[3] - r[2] - r[1] + r[0]) for r in rates]
            compare_summary(strata['coverage_interaction_pp'], interaction, load + ':interaction')
            for mode in modes:
                selected = [lookup[b, load, mode] for b in range(4)]
                for field in ['samples', 'received', 'fresh_completions', 'current_delivery_cues', 'source_cues', 'cue_violations']:
                    source = 'bad_cues' if field == 'cue_violations' else field
                    value = strata['cells'][mode][field]
                    need(type(value) is int and value == sum(int(r[source]) for r in selected), load + ':' + mode + ':' + field)
    return dict(status='PASS_POSTHOC_ARITHMETIC_CHECK' if not errors else 'FAIL_POSTHOC_ARITHMETIC_CHECK',
                errors=errors, numeric_comparisons=comparisons, empirical_decision='HOLD_CUE_INTEGRITY')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cases', type=Path)
    parser.add_argument('result', type=Path)
    args = parser.parse_args()
    try:
        report = check(args.cases, args.result)
    except (KeyError, ValueError, TypeError, OSError, IndexError, ArithmeticError) as exc:
        report = dict(status='FAIL_POSTHOC_ARITHMETIC_CHECK', errors=[type(exc).__name__ + ': ' + str(exc)])
    print(json.dumps(report, sort_keys=True))
    return 0 if not report['errors'] else 2

if __name__ == '__main__':
    raise SystemExit(main())
