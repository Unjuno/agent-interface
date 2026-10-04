import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parent

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def main():
    errors = []
    manifest = ROOT / 'SHA256SUMS'
    rows = manifest.read_text().splitlines()
    for row in rows:
        expected, relative = row.split('  ', 1)
        path = ROOT / relative
        if not path.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError('manifest escapes package')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            errors.append(relative + ':hash')
    actual_paths = {str(p.relative_to(ROOT)).replace('\\', '/') for p in ROOT.rglob('*')
                    if p.is_file() and p.name != 'SHA256SUMS' and '__pycache__' not in p.parts}
    if actual_paths != {row.split('  ', 1)[1] for row in rows}:
        errors.append('manifest:coverage')
    oracle = module('review_oracle', ROOT / 'oracle_v2.py')
    for arm, aliases in (('base', 26), ('head', 0)):
        raw = json.loads((ROOT / (arm + '.json')).read_text())
        verdict = oracle.audit(raw)
        if verdict['errors'] or verdict['malformed_execute_entries'] != aliases:
            errors.append(arm + ':oracle')
        source = ROOT / 'sources' / arm / 'runtime/core_v1/compiled_gui.py'
        if raw['source_sha256'] != hashlib.sha256(source.read_bytes()).hexdigest():
            errors.append(arm + ':source')
        retained = json.loads((ROOT / (arm + '-audit-v2.json')).read_text())
        if retained['errors'] or not all(retained['corruption_controls_rejected'].values()):
            errors.append(arm + ':controls')
    auditor = module('original_author_auditor', ROOT / 'author-v1/audit.py')
    original = json.loads((ROOT / 'author-v1/after.json').read_text())
    if auditor.audit(original)['errors']:
        errors.append('original-author-control')
    assay = json.loads((ROOT / 'author-audit-type-assay.json').read_text())
    for variant in assay['variants']:
        payload = (ROOT / (variant['label'] + '.json')).read_bytes()
        if hashlib.sha256(payload).hexdigest() != variant['raw_sha256']:
            errors.append(variant['label'] + ':hash')
        verdict = auditor.audit(json.loads(payload))
        if verdict != variant['auditor_result'] or verdict['errors']:
            errors.append(variant['label'] + ':counterexample')
    exports = json.loads((ROOT / 'export.json').read_text())
    if len(exports['files']) != 58 or not all(x['match'] for x in exports['files']):
        errors.append('author-manifest')
    print(json.dumps({'status': 'PASS_SCOPED_REVIEW_PACKAGE' if not errors else 'FAIL',
                      'manifest_files': len(rows), 'rows_per_source': 180,
                      'author_type_counterexamples': 3, 'errors': errors}, sort_keys=True))
    raise SystemExit(bool(errors))

if __name__ == '__main__':
    main()
