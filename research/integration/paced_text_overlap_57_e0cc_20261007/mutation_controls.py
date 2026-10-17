"""Reproduce targeted audit sensitivity using temporary copies of retained raw."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
from verify_saved import HERE, extract, read, require


def main():
    with tempfile.TemporaryDirectory(prefix='paced-mutations-') as temporary:
        root = Path(temporary)
        package, raw = root / 'package', root / 'raw'
        package.mkdir(); raw.mkdir()
        extract(HERE / 'frozen-source.tar.gz', package)
        extract(HERE / 'guest-output-first.tar.gz', raw)
        raw = raw / 'run-01'
        spec = importlib.util.spec_from_file_location('saved_auditor', package / 'audit.py')
        auditor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auditor)
        baseline = auditor.audit(package, raw)
        mutations = [
            ('driver_exit', 'invocations.json', lambda d: d[0].update(returncode=9), 'driver:held_a_unpaced'),
            ('omit_invocation', 'invocations.json', lambda d: d.pop(), 'exact six ordered invocations'),
            ('nonneutral_keymap', 'held_a_paced/record.json', lambda d: d['final_keymap'].__setitem__(0, 1),
             'held_a_paced: independent final neutral'),
            ('prefix_requests', 'held_a_paced/record.json',
             lambda d: d['text_boundaries'][0].update(request_end=d['text_boundaries'][0]['request_start']),
             'held_a_paced: partial text prefix before failure'),
            ('unclean_child_exit', 'unheld_unpaced/record.json', lambda d: d['app_exit'].update(returncode=-9),
             'unheld_unpaced: app_exit'),
        ]
        reports = []
        for name, path, mutate, expected in mutations:
            out = root / name
            shutil.copytree(raw, out)
            target = out / path
            data = read(target); mutate(data); target.write_text(json.dumps(data))
            report = auditor.audit(package, out)
            require(expected in report['failures'] and expected not in baseline['failures'], name)
            reports.append(dict(name=name, expected_additional_failure=expected,
                                detected=True, decision=report['decision']))
        modified = root / 'modified-source'
        shutil.copytree(package, modified)
        target = modified / 'source/runtime/backends/x11_v1/backend.py'
        target.write_bytes(target.read_bytes() + b'\n# deliberate audit-only mutation\n')
        report = auditor.audit(modified, raw)
        expected = 'source:runtime/backends/x11_v1/backend.py'
        require(expected in report['failures'] and expected not in baseline['failures'], 'changed source')
        reports.append(dict(name='changed_source', expected_additional_failure=expected,
                            detected=True, decision=report['decision']))
        first = read(HERE / 'mutation-audit.json')
        require(first['baseline'] == baseline and first['mutations'] == reports, 'mutation report mismatch')
    print(json.dumps({'targeted_additional_failures_reproduced': len(reports),
                      'baseline_remains': 'FAIL_OR_HOLD', 'native_input': False}))


if __name__ == '__main__':
    main()
