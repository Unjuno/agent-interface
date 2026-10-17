"""Read-only preservation check; never executes the native runner."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def extract(archive, destination):
    with tarfile.open(archive) as bundle:
        for item in bundle.getmembers():
            name = Path(item.name)
            require(not name.is_absolute() and '..' not in name.parts, 'unsafe path')
            require(item.isfile() or item.isdir(), 'unexpected archive member')
        bundle.extractall(destination, filter='data')


def main():
    manifest = read(HERE / 'evidence-manifest.json')
    for name, item in manifest.items():
        data = (HERE / name).read_bytes()
        require(len(data) == item['bytes'], 'size mismatch: ' + name)
        require(hashlib.sha256(data).hexdigest() == item['sha256'], 'hash mismatch: ' + name)
    source_manifest = read(HERE / 'source-manifest.json')
    require(hashlib.sha256((HERE / 'frozen-source.tar.gz').read_bytes()).hexdigest()
            == source_manifest['archive_sha256'], 'frozen archive mismatch')
    with tempfile.TemporaryDirectory(prefix='paced-preservation-') as temporary:
        package, raw = Path(temporary) / 'package', Path(temporary) / 'raw'
        package.mkdir(); raw.mkdir()
        extract(HERE / 'frozen-source.tar.gz', package)
        extract(HERE / 'guest-output-first.tar.gz', raw)
        expected = {item['path']: item for item in source_manifest['files']}
        actual = {str(p.relative_to(package)) for p in package.rglob('*') if p.is_file()}
        require(actual == set(expected), 'source membership mismatch')
        for name, item in expected.items():
            data = (package / name).read_bytes()
            require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest()
                    == item['sha256'], 'source member mismatch: ' + name)
        spec = importlib.util.spec_from_file_location('frozen_saved_auditor', package / 'audit.py')
        auditor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auditor)
        report = auditor.audit(package, raw / 'run-01')
        require(report == read(HERE / 'audit-first.json'), 'first audit no longer reproduces')
        require(report['decision'] == 'FAIL_OR_HOLD' and report['checks'] == 99
                and len(report['failures']) == 12, 'unexpected scientific result')
        mutations = read(HERE / 'mutation-audit.json')
        require(len(mutations['mutations']) == 6 and all(r['detected'] for r in mutations['mutations']),
                'mutation receipt mismatch')
        require(read(HERE / 'resource-final.json')['state'] == 'stopped', 'resource receipt mismatch')
    print(json.dumps({'preservation': 'PASS', 'scientific_result': report['decision'],
                      'checks': report['checks'], 'failed_checks': len(report['failures']),
                      'native_input_executed_by_verifier': False}))


if __name__ == '__main__':
    main()
