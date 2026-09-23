"""Run the native integration contract suites locally or in CI, without GUI/model calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SUITES = {
    'protocol': ['runtime.cli_v1.test_observe', 'runtime.selector_v1.test_selector',
                 'runtime.cli_v1.test_mcp_server', 'runtime.cli_v1.test_cli', 'runtime.core_v1.test_contract', 'runtime.cli_v1.test_review', 'test_agent_review', 'test_receipt_references', 'test_native_exchange_v1', 'test_native_mcp_v1',
                 'test_native_allocation_v1', 'test_native_mcp_relay_v1'],
    'harness': ['runtime.backends.x11_v1.test_text_plan', 'runtime.backends.x11_v1.test_partial_execution', 'test_native_finish_after_v1', 'test_native_cleanup_v1',
                'test_native_handle_bridge_v1', 'test_native_tail_v1'],
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol-python', default=sys.executable)
    parser.add_argument('--harness-python', default=sys.executable)
    parser.add_argument('--output', type=Path, required=True, help='fresh directory for full logs and result.json')
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
               PYTHONPATH=os.pathsep.join([str(ROOT), str(ROOT/'research/live_control')]))
    results = []
    for name, modules in SUITES.items():
        python = args.protocol_python if name == 'protocol' else args.harness_python
        command = [python, '-m', 'unittest', '-v', *modules]
        started = time.monotonic_ns()
        try:
            result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except OSError as error:
            code, stdout, stderr = 127, b'', (str(error)+'\n').encode()
        ended = time.monotonic_ns()
        logs = {}
        for stream, data in [('stdout', stdout), ('stderr', stderr)]:
            path = out/f'{name}.{stream}.log'
            path.write_bytes(data)
            logs[stream] = {'file': path.name, 'sha256': hashlib.sha256(data).hexdigest()}
            print(data.decode('utf-8', errors='replace'), end='', flush=True)
        results.append({'suite': name, 'command': command, 'returncode': code,
                        'duration_ns': ended-started, 'logs': logs})
    passed = all(r['returncode'] == 0 for r in results)
    report = {'schema': 'agent-interface/local-native-check-v1',
              'status': 'PASS' if passed else 'FAIL', 'suites': results,
              'scope': 'contract tests; not a live GUI experiment or independent adoption audit',
              'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (out/'result.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'report': str(out/'result.json')}))
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
