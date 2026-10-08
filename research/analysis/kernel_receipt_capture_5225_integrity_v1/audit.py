"""Separate implementation checks retained report and exact frozen Git objects."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / '.git').exists())


def inspect(report, freeze, git):
    errors = []
    rows = report.get('evidence', [])
    if (type(rows) is not list or len(rows) != len(freeze['evidence'])
            or {r.get('path') for r in rows if isinstance(r, dict)} != set(freeze['evidence'])):
        return ['evidence_inventory']
    for row in rows:
        path = row['path']
        pin = freeze['evidence'][path]
        raw = subprocess.check_output([git, 'show', freeze['source_commit'] + ':' + path], cwd=ROOT)
        actual = hashlib.sha256(raw).hexdigest()
        blob = subprocess.check_output([git, 'hash-object', '--stdin'], input=raw, cwd=ROOT).decode().strip()
        if not (actual == pin['git_sha256'] == row.get('sha256')
                and blob == pin['git_blob'] == row.get('blob') and row.get('matches') is True):
            errors.append('evidence_identity:' + path)
    matrix = freeze['matrix']
    raw = subprocess.check_output([git, 'cat-file', 'blob', freeze['evidence'][matrix['path']]['git_blob']], cwd=ROOT)
    crlf = b'\r\n'.join(raw.split(b'\n'))
    if hashlib.sha256(crlf).hexdigest() != matrix['historical_manifest_sha256']:
        errors.append('serialization_relation')
    checks = report.get('checks', {})
    positive = {'canonical_lf_matches', 'historical_crlf_matches', 'merge_and_intake_matrix_identical',
                'all_evidence_pins_match', 'all_40_distinct_mutations_held', 'historical_scientific_limits_preserved'}
    if any(checks.get(key) is not True for key in positive) or checks.get('historical_exact_git_match') is not False:
        errors.append('checks')
    if (checks.get('canonical_lf_sha256') != hashlib.sha256(raw).hexdigest()
            or checks.get('reconstructed_crlf_sha256') != hashlib.sha256(crlf).hexdigest()):
        errors.append('reported_hashes')
    if (report.get('source_commit') != freeze['source_commit'] or report.get('passed') is not True
            or report.get('disposition') != 'PASS_CAPTURE_SERIALIZATION_SCOPED'):
        errors.append('scope_or_disposition')
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--git', default='git')
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    freeze = json.loads((HERE / 'FREEZE.json').read_bytes())
    report = json.loads(args.report.read_bytes())
    errors = inspect(report, freeze, args.git)
    controls = {}
    for label in ('drop_row', 'forge_hash', 'flip_match', 'promote_scope', 'null_check'):
        copy = json.loads(json.dumps(report))
        if label == 'drop_row': copy['evidence'].pop()
        if label == 'forge_hash': copy['evidence'][0]['sha256'] = '0' * 64
        if label == 'flip_match': copy['evidence'][0]['matches'] = False
        if label == 'promote_scope': copy['disposition'] = 'PASS_RUNTIME'
        if label == 'null_check': copy['checks']['historical_crlf_matches'] = None
        controls[label] = bool(inspect(copy, freeze, args.git))
    passed = not errors and all(controls.values())
    print(json.dumps({'passed': passed, 'errors': errors, 'corruption_controls': controls,
                      'report_sha256': hashlib.sha256(args.report.read_bytes()).hexdigest(),
                      'scope': 'separate Git-byte and report-identity audit; no historical study import'}, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
