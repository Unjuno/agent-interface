"""Read-only Git-byte verification; never import or rerun the historical study."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / '.git').exists())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def matrix_check(raw, canonical_digest, historical_digest):
    # Only the already pinned LF bytes are eligible for this explanation.
    canonical = b'\r' not in raw and sha(raw) == canonical_digest
    reconstructed = raw.replace(b'\n', b'\r\n')
    return {
        'canonical_lf_sha256': sha(raw),
        'reconstructed_crlf_sha256': sha(reconstructed),
        'canonical_lf_matches': canonical,
        'historical_crlf_matches': canonical and sha(reconstructed) == historical_digest,
        'historical_exact_git_match': sha(raw) == historical_digest,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--git', default='git')
    args = parser.parse_args()
    freeze = json.loads((HERE / 'FREEZE.json').read_bytes())
    def git(*arguments):
        return subprocess.check_output([args.git, *arguments], cwd=ROOT)
    rows = []
    for path, pin in freeze['evidence'].items():
        blob = git('rev-parse', freeze['source_commit'] + ':' + path).decode().strip()
        raw = git('cat-file', 'blob', blob)
        rows.append({'path': path, 'blob': blob, 'sha256': sha(raw),
                     'matches': blob == pin['git_blob'] and sha(raw) == pin['git_sha256']})
    matrix = freeze['matrix']
    raw = git('show', freeze['source_commit'] + ':' + matrix['path'])
    historical_raw = git('show', freeze['historical_merge_commit'] + ':' + matrix['path'])
    checks = matrix_check(raw, matrix['git_sha256'], matrix['historical_manifest_sha256'])
    checks['merge_and_intake_matrix_identical'] = historical_raw == raw
    checks['all_evidence_pins_match'] = len(rows) == 15 and all(r['matches'] for r in rows)
    matrix_data = json.loads(raw)
    expected = {(key, mutation) for key in freeze['required_fields']
                for mutation in ('missing', 'null', 'string', 'integer')}
    mutations = matrix_data['mutation_matrix']
    checks['all_40_distinct_mutations_held'] = (
        len(mutations) == 40 and {(r['key'], r['mutation']) for r in mutations} == expected
        and all(r['disposition'] == 'HOLD_SCHEMA' for r in mutations))
    checks['historical_scientific_limits_preserved'] = (
        matrix_data['disposition'] == 'PASS_AUDITOR_GAP_SCOPED'
        and matrix_data['strict_original_record']['disposition'] == 'HOLD_SCHEMA'
        and matrix_data['strict_complete_schema_control']['disposition'] == 'HOLD_CONTRACT_AMBIGUITY')
    passed = (all(value for key, value in checks.items() if key.endswith('matches')
                  or key in {'merge_and_intake_matrix_identical', 'all_evidence_pins_match',
                             'all_40_distinct_mutations_held', 'historical_scientific_limits_preserved'})
              and checks['historical_exact_git_match'] is False)
    output = {'schema': 'capture-serialization-5225-v1', 'source_commit': freeze['source_commit'],
              'checks': checks, 'evidence': rows, 'passed': passed,
              'disposition': 'PASS_CAPTURE_SERIALIZATION_SCOPED' if passed else 'HOLD_CAPTURE_IDENTITY',
              'scope': 'exact retained Git-byte serialization explanation only; original verifier remains failing; no scientific or runtime promotion'}
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
