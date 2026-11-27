import json
import hashlib
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path('/src')
ATTEMPT = ROOT / 'research/live_control/wslc_fake_x_public_currentmain_20261024_s10'
OUT = Path('/out')
ENV = os.environ.copy()
ENV['PYTHONPATH'] = '/src:/deps'
PROBE = ATTEMPT / 'probe.py'
AUDIT = ATTEMPT / 'audit.py'

dependency_manifest = json.loads((ATTEMPT / 'inputs/DEPENDENCIES.json').read_text(encoding='utf-8'))
for item in dependency_manifest['files']:
    actual = hashlib.sha256((Path('/deps') / item['path']).read_bytes()).hexdigest()
    assert actual == item['sha256'], 'dependency hash mismatch: ' + item['path']
sys.path.insert(0, '/deps')
import Xlib  # noqa: E402 - checked only after the exact source hashes above
import six  # noqa: E402
print(json.dumps({'stage': 'dependencies_verified',
                  'python_xlib': dependency_manifest['python_xlib'],
                  'six': dependency_manifest['six'],
                  'file_count': len(dependency_manifest['files']),
                  'xlib_module': Xlib.__file__, 'six_module': six.__file__},
                 sort_keys=True), flush=True)


def run_probe(optimized, output_name):
    argv = [str(PROBE), '--output', str(OUT / output_name)]
    bootstrap = (
        "import runpy,sys;sys.path.insert(0,'/src');"
        f"sys.argv={argv!r};runpy.run_path({str(PROBE)!r},run_name='__main__')"
    )
    command = [sys.executable]
    if optimized:
        command.append('-O')
    command += ['-B', '-c', bootstrap]
    print(json.dumps({'stage': 'probe', 'optimized': optimized,
                      'argv': command}, sort_keys=True), flush=True)
    subprocess.run(command, env=ENV, check=True)


def run_audit(input_name, output_name):
    command = [sys.executable, '-B', str(AUDIT), str(OUT / input_name),
               '--output', str(OUT / output_name)]
    print(json.dumps({'stage': 'audit', 'argv': command}, sort_keys=True), flush=True)
    subprocess.run(command, env=ENV, check=True)


run_probe(False, 'normal.json')
run_audit('normal.json', 'normal-audit.json')
run_probe(True, 'optimized.json')
run_audit('optimized.json', 'optimized-audit.json')

results = {}
for name in ('normal', 'optimized'):
    report = json.loads((OUT / f'{name}.json').read_text(encoding='utf-8'))
    audit = json.loads((OUT / f'{name}-audit.json').read_text(encoding='utf-8'))
    assert audit['status'] == 'PASS_CHARACTERIZATION_NOT_RELEASE_BOUND'
    assert audit['checks_passed'] == 26
    assert audit['mutation_controls_rejected'] == 4
    assert [case['mode'] for case in report['cases']] == [
        'healthy', 'focus_query', 'release_sync']
    assert report['real_x_connection'] is False
    assert report['live_allocation_invocations'] == 0
    assert audit['physical_release_proven'] is False
    assert audit['cancellation_tested'] is False
    results[name] = {'audit_status': audit['status'],
                     'checks_passed': audit['checks_passed'],
                     'mutation_controls_rejected': audit['mutation_controls_rejected'],
                     'python': report['python'], 'platform': report['platform']}

summary = {'status': 'PASS_PORTABILITY_SCOPED', 'python': sys.version,
           'platform': platform.platform(), 'results': results,
           'nonclaims': ['no real X connection', 'no physical input release',
                         'no cancellation', 'no live application or MAP01']}
(OUT / 'runner-summary.json').write_text(
    json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps({'stage': 'complete', 'summary': summary}, sort_keys=True), flush=True)

