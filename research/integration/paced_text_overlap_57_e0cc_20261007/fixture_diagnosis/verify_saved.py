"""Read retained diagnostic data only; never dispatch native input."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
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
            path = Path(item.name)
            require(not path.is_absolute() and '..' not in path.parts, 'unsafe archive path')
            require(item.isfile() or item.isdir(), 'unexpected archive member')
        bundle.extractall(destination, filter='data')


def main():
    for name, item in read(HERE / 'manifest.json').items():
        data = (HERE / name).read_bytes()
        require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'], name)
    with tempfile.TemporaryDirectory(prefix='tk-target-readonly-') as temporary:
        root = Path(temporary)
        package, raw = root / 'package', root / 'raw'
        package.mkdir(); raw.mkdir()
        extract(HERE / 'source-first.tar.gz', package)
        extract(HERE / 'raw-first.tar.gz', raw)
        raw = raw / 'run-01'
        freeze = read(package / 'source-freeze.json')
        expected = {i['path'] for i in freeze['files']} | {'source-freeze.json'}
        require(expected == {str(f.relative_to(package)) for f in package.rglob('*') if f.is_file()}, 'source membership')
        for item in freeze['files']:
            data = (package / item['path']).read_bytes()
            require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'], item['path'])
        with tarfile.open(HERE.parent / 'frozen-source.tar.gz') as original:
            require(original.extractfile('recipient.py').read() == (package / 'recipient.py').read_bytes(),
                    'recipient changed from failed construction')
            require(original.extractfile('source-lock.json').read() == (package / 'source-lock.json').read_bytes(),
                    'backend/core identity changed')
        spec = importlib.util.spec_from_file_location('saved_diagnostic_audit', package / 'audit.py')
        auditor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auditor)
        report = auditor.audit(package, raw)
        require(report == read(HERE / 'audit-first.json') and report['checks'] == 48 and not report['failures'], 'first audit')
        mutations = [
            ('wrong_native_focus', 'wrapper_target/record.json',
             lambda d: d['text_boundaries'][0].update(native_focus_before=d['target']['widget']),
             'wrapper_target: native focus before input'),
            ('missing_app_effect', 'wrapper_target/effect.json', lambda d: d.update(text=''), 'wrapper_target: text effect'),
            ('nonneutral_final', 'wrapper_target/record.json', lambda d: d['final_keymap'].__setitem__(0, 1), 'wrapper_target: final neutral'),
            ('bad_driver_exit', 'invocations.json', lambda d: d[1].update(returncode=1), 'wrapper_target: driver'),
        ]
        receipts = []
        for name, path, mutate, expected_failure in mutations:
            target = root / name
            shutil.copytree(raw, target)
            file = target / path
            value = read(file); mutate(value); file.write_text(json.dumps(value))
            result = auditor.audit(package, target)
            require(result['decision'] == 'HOLD' and expected_failure in result['failures'], name)
            receipts.append(dict(name=name, expected_failure=expected_failure, result=result))
        require(receipts == read(HERE / 'mutation-results.json'), 'mutation receipts')
        require(read(HERE / 'vm-stop-receipt.json')['state'] == 'stopped', 'VM receipt')
    print(json.dumps({'preservation': 'PASS', 'diagnosis': report['decision'], 'checks': 48,
                      'corruption_controls': 4, 'original_six_cell_result': 'FAIL_OR_HOLD',
                      'native_input_executed': False}))


if __name__ == '__main__':
    main()
