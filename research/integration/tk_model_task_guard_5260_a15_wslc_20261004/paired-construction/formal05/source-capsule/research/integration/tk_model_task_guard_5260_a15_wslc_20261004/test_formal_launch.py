import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

from formal_launch import digest, finish_capture, launch, start_capture, validate_outer_plan


class FormalLaunchCaptureTests(unittest.TestCase):
    def test_frozen_formal_plan_checks_source_model_schema_slots_and_container(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'formal'
            source_root, capsule = root / 'source', root / 'source-capsule'
            for directory in (root, source_root, capsule):
                directory.mkdir(parents=True, exist_ok=True)
            source_files = {
                '/src/research/integration/tk_model_task_guard_5260_a15_wslc_20261004/formal_launch.py':
                    Path(__import__('formal_launch').__file__),
                '/src/research/integration/tk_model_task_guard_5260_a15_wslc_20261004/file_exchange.py':
                    Path(__file__).with_name('formal_launch.py'),
            }
            source_hashes = {}
            for logical, original in source_files.items():
                relative = Path(*logical.removeprefix('/src/').split('/'))
                for base in (source_root, capsule):
                    target = base / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(original.read_bytes())
                source_hashes[logical] = digest(original.read_bytes())
            schema = root / 'response.schema.json'
            schema.write_bytes(b'{"type":"object"}\n')
            codex = root / 'codex.exe'
            codex.write_bytes(b'frozen fake codex\n')
            plan = {'schema': 'a15-live-paired-study-v1', 'allocation': 'test-allocation',
                'formal_allocation': True, 'model': {'name': 'gpt-5.6-luna', 'effort': 'low'},
                'rows': [{'id': f'pair-{index:03d}'} for index in range(4)],
                'source_sha256': source_hashes}
            plan_blob = json.dumps(plan).encode() + b'\n'
            (root / 'plan.json').write_bytes(plan_blob)
            freeze = digest(plan_blob)
            slots = {}
            for row in plan['rows']:
                for kind in ('first', 'recovery'):
                    slot = row['id'] + '-' + kind
                    workdir = root / 'host-working' / slot
                    workdir.mkdir(parents=True)
                    slots[slot] = {'argv': [str(codex), '--model', 'gpt-5.6-luna',
                        '--config', 'model_reasoning_effort="low"', '--output-schema', str(schema),
                        '--image', str(root / 'exchange' / slot / 'image' / 'payload.png'),
                        '--cd', str(workdir)],
                        'schema_sha256': digest(schema.read_bytes()), 'timeout_seconds': 60}
            host_plan = {'allocation': plan['allocation'], 'freeze_sha256': freeze,
                'executable_sha256': digest(codex.read_bytes()), 'plans': slots}
            host_blob = json.dumps(host_plan).encode() + b'\n'
            (root / 'host-plan.json').write_bytes(host_blob)
            host_script = source_root / 'research/integration/tk_model_task_guard_5260_a15_wslc_20261004/file_exchange.py'
            launcher = Path(__import__('formal_launch').__file__)
            wslc = root / 'wslc.exe'
            wslc.write_text('#!/bin/sh\nexit 0\n', encoding='utf-8')
            wslc.chmod(0o755)
            source_mount = 'type=bind,source=' + str(source_root).replace('\\', '/') + ',target=/src,readonly'
            output_mount = 'type=bind,source=' + str(root).replace('\\', '/') + ',target=/out'
            candidate_argv = [str(wslc), 'run', '--rm', '--pull', 'never', '--network', 'none',
                '--cpus', '0.5', '--memory', '512M', '--user', '65534:65534',
                '--mount', source_mount, '--mount', output_mount, '--workdir', '/src',
                'sha256:' + '0' * 64,
                '/src/research/integration/tk_model_task_guard_5260_a15_wslc_20261004/construction_x11.py',
                '--study', '/out/plan.json', '/out/candidate', '/out/exchange']
            config = {'schema': 'a15-formal-outer-launch-v1', 'root': str(root),
                'source_root': str(source_root), 'plan_sha256': freeze,
                'host_plan_sha256': digest(host_blob), 'launcher_sha256': digest(launcher.read_bytes()),
                'python_executable': sys.executable, 'host_script': str(host_script),
                'host_argv': [sys.executable, '-B', str(host_script), str(root / 'host-plan.json')],
                'host_timeout_seconds': 840, 'candidate_output': str(root / 'candidate'),
                'candidate_argv': candidate_argv, 'candidate_timeout_seconds': 900,
                'host_ready_timeout_seconds': 10, 'codex_executable': str(codex),
                'codex_sha256': digest(codex.read_bytes()), 'container_image_digest': '0' * 64,
                'response_schema_sha256': digest(schema.read_bytes())}
            config_path = root / 'outer-plan.json'
            config_path.write_text(json.dumps(config), encoding='utf-8')
            self.assertEqual(validate_outer_plan(config_path), config)
            duplicate_override = dict(config)
            duplicate_override['candidate_argv'] = list(candidate_argv)
            network_index = duplicate_override['candidate_argv'].index('--network')
            duplicate_override['candidate_argv'][network_index:network_index+2] = [
                '--network', 'none', '--network', 'bridge']
            config_path.write_text(json.dumps(duplicate_override), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'FORMAL_CONTAINER_COMMAND_NOT_PINNED'):
                validate_outer_plan(config_path)

    def test_formal_source_capsule_drift_is_denied_before_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'formal'
            root.mkdir()
            source_root = root / 'source'
            capsule = root / 'source-capsule'
            source_root.mkdir()
            source_file = source_root / 'host_stub.py'
            source_file.write_bytes(b'expected source\n')
            frozen = digest(source_file.read_bytes())
            capsule_file = capsule / 'host_stub.py'
            capsule_file.parent.mkdir()
            capsule_file.write_bytes(b'tampered source\n')
            plan_blob = json.dumps({'allocation': 'test-allocation',
                'formal_allocation': True, 'model': {'name': 'model', 'effort': 'low'},
                'source_sha256': {'/src/host_stub.py': frozen}}).encode() + b'\n'
            host_plan_blob = json.dumps({'allocation': 'test-allocation',
                'freeze_sha256': digest(plan_blob)}).encode() + b'\n'
            (root / 'plan.json').write_bytes(plan_blob)
            (root / 'host-plan.json').write_bytes(host_plan_blob)
            (root / 'response.schema.json').write_bytes(b'{}\n')
            (root / 'host_stub.py').write_bytes(b'host stub\n')
            config = {'schema': 'a15-formal-outer-launch-v1', 'root': str(root),
                'source_root': str(source_root), 'plan_sha256': digest(plan_blob),
                'host_plan_sha256': digest(host_plan_blob),
                'launcher_sha256': digest(Path(__import__('formal_launch').__file__).read_bytes()),
                'python_executable': sys.executable,
                'host_script': str(root / 'host_stub.py'),
                'host_argv': [sys.executable, '-c', 'raise SystemExit(0)'],
                'host_timeout_seconds': 5,
                'candidate_output': str(root / 'candidate'),
                'candidate_argv': [sys.executable, '-c', 'raise SystemExit(0)'],
                'candidate_timeout_seconds': 5, 'host_ready_timeout_seconds': 5,
                'codex_executable': sys.executable,
                'codex_sha256': digest(Path(sys.executable).read_bytes()),
                'container_image_digest': '0' * 64,
                'response_schema_sha256': digest((root / 'response.schema.json').read_bytes())}
            config_path = root / 'outer-plan.json'
            config_path.write_text(json.dumps(config), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'FORMAL_SOURCE_CAPSULE_CHANGED'):
                validate_outer_plan(config_path)
            self.assertFalse((root / 'host-launch').exists())
            self.assertFalse((root / 'candidate-launch').exists())

    def test_finite_fake_pair_captures_both_outer_launches_before_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'formal'
            root.mkdir()
            source = root / 'source'
            source.mkdir()
            plan_blob = b'{"allocation":"test-allocation"}\n'
            freeze = digest(plan_blob)
            (root / 'plan.json').write_bytes(plan_blob)
            host_plan_blob = json.dumps({'allocation': 'test-allocation',
                'freeze_sha256': freeze}).encode() + b'\n'
            (root / 'host-plan.json').write_bytes(host_plan_blob)
            (source / 'host_stub.py').write_text('# frozen fixture\n', encoding='utf-8')
            host_code = ("from pathlib import Path;Path(r'" + str(root / 'host' / 'host-plan')
                + "').parent.mkdir(parents=True);Path(r'" + str(root / 'host' / 'host-plan')
                + "').write_bytes(b'host-ready')")
            candidate_code = ("from pathlib import Path;Path(r'" + str(root / 'candidate')
                + "').mkdir()")
            config = {'schema': 'a15-formal-outer-launch-v1', 'root': str(root),
                'source_root': str(source), 'plan_sha256': digest(plan_blob),
                'host_plan_sha256': digest(host_plan_blob),
                'launcher_sha256': digest(Path(__import__('formal_launch').__file__).read_bytes()),
                'python_executable': sys.executable,
                'host_script': str(source / 'host_stub.py'),
                'host_argv': [sys.executable, '-c', host_code],
                'host_timeout_seconds': 5,
                'candidate_output': str(root / 'candidate'),
                'candidate_argv': [sys.executable, '-c', candidate_code],
                'candidate_timeout_seconds': 5, 'host_ready_timeout_seconds': 5,
                'codex_executable': sys.executable,
                'codex_sha256': digest(Path(sys.executable).read_bytes()),
                'container_image_digest': '0' * 64,
                'response_schema_sha256': digest(b'')}
            config_path = root / 'outer-plan.json'
            config_path.write_text(json.dumps(config), encoding='utf-8')
            result = launch(config_path)
            self.assertEqual(result['status'], 'COMPLETE')
            for role in ('host-launch', 'candidate-launch'):
                directory = root / role
                attempt = json.loads((directory / 'attempt.json').read_bytes())
                receipt = json.loads((directory / 'receipt.json').read_bytes())
                self.assertEqual(receipt['argv'], attempt['argv'])
                self.assertEqual(receipt['exit_code'], 0)
                for name in ('attempt.json', 'stdout.bin', 'stderr.bin'):
                    self.assertEqual(receipt['output_sha256'][name],
                        digest((directory / name).read_bytes()))

    def test_capture_retains_exact_streams_and_joined_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'candidate-launch'
            capture = start_capture(
                [sys.executable, '-c',
                 "import sys;sys.stdout.buffer.write(b'out\\x00');sys.stderr.buffer.write(b'err\\x00')"],
                Path.cwd(), directory)
            receipt = finish_capture(capture, timeout_seconds=5)
            attempt = json.loads((directory / 'attempt.json').read_bytes())
            self.assertEqual(receipt['exit_code'], 0)
            self.assertIsNone(receipt['launch_error'])
            self.assertFalse(receipt['timed_out'])
            self.assertTrue(all(receipt[key] == value for key, value in attempt.items()))
            self.assertEqual((directory / 'stdout.bin').read_bytes(), b'out\x00')
            self.assertEqual((directory / 'stderr.bin').read_bytes(), b'err\x00')
            self.assertEqual(receipt['output_sha256']['stdout.bin'],
                             hashlib.sha256(b'out\x00').hexdigest())

    def test_existing_attempt_is_refused_before_command_start(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'candidate-launch'
            directory.mkdir()
            (directory / 'attempt.json').write_bytes(b'owned\n')
            with self.assertRaisesRegex(ValueError, 'LAUNCH_EVIDENCE_EXISTS'):
                start_capture([sys.executable, '-c', 'raise SystemExit(99)'],
                              Path.cwd(), directory)
            self.assertEqual((directory / 'attempt.json').read_bytes(), b'owned\n')

    def test_timeout_is_recorded_and_process_is_reaped(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'candidate-launch'
            capture = start_capture(
                [sys.executable, '-c', 'import time;time.sleep(30)'],
                Path.cwd(), directory)
            receipt = finish_capture(capture, timeout_seconds=0.05)
            self.assertTrue(receipt['timed_out'])
            self.assertIsNotNone(receipt['exit_code'])
            self.assertIsNone(receipt['launch_error'])
            self.assertTrue((directory / 'receipt.json').is_file())


if __name__ == '__main__':
    unittest.main()
