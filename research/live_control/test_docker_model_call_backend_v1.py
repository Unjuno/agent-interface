import os
import json
import subprocess
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from docker_model_call_backend_v1 import (build_command, build_preflight_command,
    call, preflight_call, preflight_identity)

class DockerBackendTest(unittest.TestCase):
    def test_task_command_selects_schema_and_instructions_per_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            runner=root/'runner.py'; image=root/'image.png'; prompt=root/'prompt.txt'; workspace=root/'workspace'; ipc=root/'ipc'
            plain_schema=root/'plain-schema.json'; compiled_schema=root/'compiled-schema.json'
            plain_instructions=root/'plain-instructions.txt'; compiled_instructions=root/'compiled-instructions.txt'
            for path in (runner,image,prompt,plain_schema,compiled_schema,plain_instructions,compiled_instructions):
                path.write_text('x')
            workspace.mkdir(); ipc.mkdir()
            values={
                'AGENT_INTERFACE_DOCKER_RUNNER':str(runner),
                'AGENT_INTERFACE_DOCKER_IMAGE':'pinned-image@sha256:abcd',
                'AGENT_INTERFACE_DOCKER_IPC':str(ipc),
                'AGENT_INTERFACE_DOCKER_SCHEMA_PLAIN':str(plain_schema),
                'AGENT_INTERFACE_DOCKER_SCHEMA_COMPILED':str(compiled_schema),
                'AGENT_INTERFACE_DOCKER_INSTRUCTIONS_PLAIN':str(plain_instructions),
                'AGENT_INTERFACE_DOCKER_INSTRUCTIONS_COMPILED':str(compiled_instructions),
            }
            with patch.dict(os.environ, values):
                plain=build_command(root/'plain-output',prompt,image,'plain',workspace)
                compiled=build_command(root/'compiled-output',prompt,image,'compiled',workspace)
            self.assertIn(f'{plain_schema.resolve()}:/repo/schema.json:ro', plain)
            self.assertIn(f'{plain_instructions.resolve()}:/repo/instructions.txt:ro', plain)
            self.assertNotIn(f'{compiled_schema.resolve()}:/repo/schema.json:ro', plain)
            self.assertIn(f'{compiled_schema.resolve()}:/repo/schema.json:ro', compiled)
            self.assertIn(f'{compiled_instructions.resolve()}:/repo/instructions.txt:ro', compiled)
            self.assertNotIn(f'{plain_schema.resolve()}:/repo/schema.json:ro', compiled)

    def test_preflight_command_uses_handle_mode_without_image(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            runner=root/'runner.py'; instructions=root/'instructions.txt'
            prompt=root/'prompt.txt'; schema=root/'schema.json'; workspace=root/'workspace'
            ipc=root/'ipc'; output=root/'result'/'model-call'
            for path in (runner, instructions, prompt, schema): path.write_text('x')
            workspace.mkdir(); ipc.mkdir(); output.parent.mkdir()
            values={
                'AGENT_INTERFACE_DOCKER_RUNNER':str(runner),
                'AGENT_INTERFACE_DOCKER_INSTRUCTIONS':str(instructions),
                'AGENT_INTERFACE_DOCKER_IMAGE':'pinned-image@sha256:abcd',
                'AGENT_INTERFACE_DOCKER_IPC':str(ipc),
            }
            with patch.dict(os.environ, values):
                command=build_preflight_command(output,prompt,workspace,instructions,schema)
                self.assertEqual(command[1:5], ['run','--rm','--network','none'])
                self.assertIn('handle', command)
                self.assertIn('-', command)
                self.assertNotIn('coordinate', command)
                self.assertNotIn('/repo/image.png', command)
                self.assertEqual(command[-4:],
                                 ['handle','-','/repo/instructions.txt','/repo/schema.json'])

    def test_preflight_cache_identity_includes_container_image(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); runner=root/'runner'; instructions=root/'instructions'
            other_instructions=root/'other-instructions'
            schema=root/'schema'; ipc=root/'ipc'
            for path in (runner,instructions,schema): path.write_text('x')
            other_instructions.write_text('changed schema-preflight instructions')
            ipc.mkdir()
            common={
                'AGENT_INTERFACE_DOCKER_RUNNER':str(runner),
                'AGENT_INTERFACE_DOCKER_INSTRUCTIONS':str(instructions),
                'AGENT_INTERFACE_DOCKER_IPC':str(ipc),
            }
            with patch.dict(os.environ,{**common,'AGENT_INTERFACE_DOCKER_IMAGE':'image:a'}):
                identity_a,key_a=preflight_identity(schema,instructions)
            with patch.dict(os.environ,{**common,'AGENT_INTERFACE_DOCKER_IMAGE':'image:b'}):
                identity_b,key_b=preflight_identity(schema,instructions)
            with patch.dict(os.environ,{**common,'AGENT_INTERFACE_DOCKER_IMAGE':'image:a'}):
                _identity_c,key_c=preflight_identity(schema,other_instructions)
            self.assertNotEqual(key_a,key_b)
            self.assertNotEqual(key_a,key_c)
            self.assertEqual(identity_a['model_boundary'],'container-to-host-model-ipc')

    def test_preflight_timeout_records_unknown_remote_state_without_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); result=root/'result'; result.mkdir()
            output=result/'model-call'
            command=['inert']
            with patch('docker_model_call_backend_v1.build_preflight_command',return_value=command), \
                 patch('docker_model_call_backend_v1.subprocess.run',
                       side_effect=subprocess.TimeoutExpired(command,90,output=b'partial')) as run:
                with self.assertRaisesRegex(RuntimeError,'STOP_DOCKER_PREFLIGHT_TIMEOUT'):
                    preflight_call(root/'prompt',root/'workspace',output,
                                   root/'instructions',root/'schema')
                run.assert_called_once()
            attempt=json.loads((result/'preflight-client-attempt.json').read_text())
            receipt=json.loads((result/'preflight-client-result.json').read_text())
            self.assertEqual(attempt['mode'],'handle')
            self.assertEqual(receipt['container_state'],'unknown')
            self.assertEqual(receipt['host_model_state'],'unknown')
            self.assertFalse(receipt['retry_performed'])
            self.assertEqual((result/'preflight-runner-stdout.txt').read_text(),'partial')

    def test_preflight_call_records_one_successful_handle_invocation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); result=root/'result'; result.mkdir()
            output=result/'model-call'
            completed=SimpleNamespace(returncode=0,stdout=b'out',stderr=b'err')
            with patch('docker_model_call_backend_v1.build_preflight_command',
                       return_value=['docker','run','handle','-']), \
                 patch('docker_model_call_backend_v1.subprocess.run',
                       return_value=completed) as run:
                actual=preflight_call(root/'prompt',root/'workspace',output,
                                      root/'instructions',root/'schema')
            run.assert_called_once_with(['docker','run','handle','-'],capture_output=True,
                                        check=False,timeout=90)
            self.assertIs(actual,completed)
            attempt=json.loads((result/'preflight-client-attempt.json').read_text())
            receipt=json.loads((result/'preflight-client-result.json').read_text())
            self.assertIsNone(attempt['image'])
            self.assertEqual(receipt['status'],'returned')
            self.assertEqual(receipt['returncode'],0)

    def test_real_local_client_timeout_reaps_only_its_direct_child(self):
        children = []
        popen = subprocess.Popen
        def tracked_popen(*args, **kwargs):
            child = popen(*args, **kwargs)
            children.append(child)
            return child

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'call'
            # Exercise subprocess.run's real timeout/kill/wait path using only
            # an owned Python sleeper, never Docker or a host-model process.
            command = [sys.executable, '-c', 'import time; time.sleep(30)']
            with patch.dict(os.environ, {'AGENT_INTERFACE_DOCKER_SCHEMA': 'unused'}), \
                 patch('docker_model_call_backend_v1.build_command', return_value=command), \
                 patch('docker_model_call_backend_v1.CLIENT_TIMEOUT_SECONDS', 0.2), \
                 patch('subprocess.Popen', side_effect=tracked_popen):
                try:
                    with self.assertRaisesRegex(RuntimeError, 'STOP_DOCKER_BACKEND_TIMEOUT'):
                        call(root, 'prompt', Path(temp)/'image', 'plain', Path(temp))
                    self.assertEqual(len(children), 1)
                    self.assertIsNotNone(children[0].returncode)
                    receipt = json.loads((root/'client-result.json').read_text())
                    self.assertEqual(receipt['container_state'], 'unknown')
                    self.assertEqual(receipt['host_model_state'], 'unknown')
                    self.assertFalse((root/'result.json').exists())
                finally:
                    for child in children:
                        if child.poll() is None:
                            child.kill()
                        child.wait(timeout=5)

    def test_client_timeout_retains_uncertainty_without_retry_or_parse(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'call'
            def expire(*args, **kwargs):
                self.assertEqual(kwargs['timeout'], 90)
                self.assertTrue((root/'client-attempt.json').is_file())
                raise subprocess.TimeoutExpired(['inert'], 90,
                    output=b'x'*2500+b'last', stderr=b'partial error')
            with patch.dict(os.environ, {'AGENT_INTERFACE_DOCKER_SCHEMA': 'unused',
                                         'AGENT_INTERFACE_MODEL_BACKEND': 'legacy'}), \
                 patch('docker_model_call_backend_v1.build_command', return_value=['inert']), \
                 patch('docker_model_call_backend_v1.subprocess.run', side_effect=expire) as run, \
                 patch('integrated_efficiency_model_v1.parse') as parse:
                with self.assertRaisesRegex(RuntimeError, 'STOP_DOCKER_BACKEND_TIMEOUT'):
                    call(root, 'prompt', Path(temp)/'image', 'plain', Path(temp))
                run.assert_called_once()
                parse.assert_not_called()
            receipt = json.loads((root/'client-result.json').read_text())
            self.assertEqual(receipt['container_state'], 'unknown')
            self.assertEqual(receipt['host_model_state'], 'unknown')
            self.assertFalse(receipt['retry_performed'])
            self.assertIsNone(receipt['returncode'])
            self.assertEqual(len((root/'runner-stdout.txt').read_text()), 2000)
            self.assertTrue((root/'runner-stdout.txt').read_text().endswith('last'))
            self.assertFalse((root/'result.json').exists())

    def test_call_validates_output_before_semantic_parse_without_retry(self):
        for answer, valid in (({"answer": "ok"}, True), ({"answer": "wrong"}, False)):
            with self.subTest(answer=answer), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                schema = root / 'schema.json'
                schema.write_text(json.dumps({
                    '$schema': 'https://json-schema.org/draft/2020-12/schema',
                    'const': {'answer': 'ok'},
                }), encoding='utf-8')
                output = root / 'call'

                def runner(*args, **kwargs):
                    retained = output / 'runner'
                    retained.mkdir()
                    (retained / 'process.json').write_text('{}')
                    rows = [
                        {'type': 'turn.completed', 'usage': {'input_tokens': 7}},
                        {'type': 'item.completed', 'item': {
                            'type': 'agent_message', 'text': json.dumps(answer)}},
                    ]
                    (retained / 'events.jsonl').write_text(
                        ''.join(json.dumps(row) + '\n' for row in rows))
                    return SimpleNamespace(returncode=0, stdout='runner output', stderr='')

                with patch.dict(os.environ, {'AGENT_INTERFACE_DOCKER_SCHEMA': str(schema),
                                             'AGENT_INTERFACE_MODEL_BACKEND': 'legacy'}), \
                     patch('docker_model_call_backend_v1.build_command', return_value=['inert']), \
                     patch('docker_model_call_backend_v1.subprocess.run', side_effect=runner) as run, \
                     patch('integrated_efficiency_model_v1.parse', return_value={'grounding': 'validated'}) as parse:
                    if valid:
                        self.assertEqual(call(output, 'prompt', root/'image', 'plain', root),
                                         {'grounding': 'validated'})
                        parse.assert_called_once_with(output/'runner', 'plain')
                        self.assertEqual(json.loads((output/'result.json').read_text()),
                                         {'grounding': 'validated'})
                    else:
                        with self.assertRaisesRegex(RuntimeError, 'STOP_SCHEMA_OUTPUT_INVALID'):
                            call(output, 'prompt', root/'image', 'plain', root)
                        parse.assert_not_called()
                        self.assertFalse((output/'result.json').exists())
                    run.assert_called_once()
                validation = json.loads((output/'schema-validation.json').read_text())
                self.assertEqual(validation['status'], 'PASS' if valid else 'STOP_SCHEMA_OUTPUT_INVALID')
                self.assertEqual((output/'runner-stdout.txt').read_text(), 'runner output')

    def test_actual_semantic_parser_preserves_grounding_and_usage(self):
        from integrated_efficiency_model_v1 import CONTRACTS
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'call'
            answer = {'format': 'plain-form-points-v1',
                      'field': {'point_space': 'source_observation_pixels', 'point': {'x': 10, 'y': 20}},
                      'submit': {'point_space': 'source_observation_pixels', 'point': {'x': 30, 'y': 40}}}
            def runner(*args, **kwargs):
                retained = root/'runner'; retained.mkdir()
                rows = [{'type': 'thread.started', 'thread_id': 'synthetic-call'},
                        {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': json.dumps(answer)}},
                        {'type': 'turn.completed', 'usage': {'input_tokens': 7, 'output_tokens': 3}}]
                (retained/'events.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
                (retained/'process.json').write_text(json.dumps({
                    'started_ns': 10, 'exited_ns': 30, 'requested_model': 'synthetic',
                    'requested_effort': 'low'}))
                return SimpleNamespace(returncode=0, stdout='', stderr='')
            with patch.dict(os.environ, {'AGENT_INTERFACE_DOCKER_SCHEMA': str(CONTRACTS['plain'][0])}), \
                 patch('docker_model_call_backend_v1.build_command', return_value=['inert']), \
                 patch('docker_model_call_backend_v1.subprocess.run', side_effect=runner) as run:
                result = call(root, 'prompt', Path(temp)/'image', 'plain', Path(temp))
                run.assert_called_once()
            self.assertEqual(result['grounding'], {'field_point': [10,20], 'submit_point': [30,40]})
            self.assertEqual(result['usage'], {'input_tokens': 7, 'output_tokens': 3})
            self.assertEqual(result['call_id'], 'synthetic-call')
            self.assertEqual(result['runner_ns'], 20)
            self.assertIsNone(result['cost'])

    def test_compiled_contract_passes_schema_gate_and_semantic_parser(self):
        from integrated_efficiency_model_v1 import CONTRACTS
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'call'
            answer = {
                'format': 'compiled-form-grounding-v1',
                'field': {'point_space': 'source_observation_pixels',
                          'point': {'x': 10, 'y': 20},
                          'motion_model': 'surface_origin_translation'},
                'submit': {'point_space': 'source_observation_pixels',
                           'point': {'x': 30, 'y': 40},
                           'motion_model': 'surface_origin_translation'},
                'method': {
                    'first_action': 'enter_exact_token',
                    'continue_when': 'field_pixels_changed_and_submit_revalidated',
                    'second_action': 'activate_submit',
                    'complete_when': 'submission_pixels_changed_then_independent_score',
                },
            }
            def runner(*args, **kwargs):
                retained = root/'runner'; retained.mkdir()
                rows = [
                    {'type': 'thread.started', 'thread_id': 'synthetic-compiled-call'},
                    {'type': 'item.completed', 'item': {
                        'type': 'agent_message', 'text': json.dumps(answer)}},
                    {'type': 'turn.completed', 'usage': {
                        'input_tokens': 11, 'output_tokens': 9}},
                ]
                (retained/'events.jsonl').write_text(
                    ''.join(json.dumps(row)+'\n' for row in rows))
                (retained/'process.json').write_text(json.dumps({
                    'started_ns': 100, 'exited_ns': 150,
                    'requested_model': 'synthetic', 'requested_effort': 'low'}))
                return SimpleNamespace(returncode=0, stdout='', stderr='')

            with patch.dict(os.environ, {
                    'AGENT_INTERFACE_DOCKER_SCHEMA': str(CONTRACTS['compiled'][0])}), \
                 patch('docker_model_call_backend_v1.build_command', return_value=['inert']), \
                 patch('docker_model_call_backend_v1.subprocess.run', side_effect=runner) as run:
                result = call(root, 'prompt', Path(temp)/'image', 'compiled', Path(temp))
                run.assert_called_once()

            self.assertEqual(json.loads((root/'schema-validation.json').read_text())['status'], 'PASS')
            self.assertEqual(result['grounding']['field_point'], [10, 20])
            self.assertEqual(result['grounding']['submit_point'], [30, 40])
            self.assertEqual(result['grounding']['method'], answer['method'])
            self.assertEqual(result['usage'], {'input_tokens': 11, 'output_tokens': 9})
            self.assertEqual(result['call_id'], 'synthetic-compiled-call')
            self.assertEqual(result['runner_ns'], 50)

    def test_call_owns_prompt_creation_and_builder_owns_output_creation(self):
        source = Path(__file__).with_name('docker_model_call_backend_v1.py').read_text()
        self.assertEqual(source.count('root.mkdir(parents=True, exist_ok=False)'), 1)

    def test_missing_mount_stops_before_docker(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); prompt=root/'p'; image=root/'i'; workspace=root/'w'; ipc=root/'ipc'
            prompt.write_text('x'); image.write_text('x'); workspace.mkdir(); ipc.mkdir()
            values={'AGENT_INTERFACE_DOCKER_RUNNER':str(root/'missing-runner'),'AGENT_INTERFACE_DOCKER_SCHEMA':str(prompt),'AGENT_INTERFACE_DOCKER_INSTRUCTIONS':str(prompt),'AGENT_INTERFACE_DOCKER_IMAGE':'test:local','AGENT_INTERFACE_DOCKER_IPC':str(ipc)}
            old={k:os.environ.get(k) for k in values}
            os.environ.update(values)
            try:
                with self.assertRaises(FileNotFoundError):
                    build_command(root/'out', prompt, image, 'compiled', workspace)
            finally:
                for k,v in old.items():
                    if v is None: os.environ.pop(k,None)
                    else: os.environ[k]=v

    def test_unconfigured_stops_before_docker(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); prompt=root/'p'; image=root/'i'; workspace=root/'w'; ipc=root/'ipc'
            for p in (prompt,image,workspace,ipc):
                if p.suffix: p.write_text('x')
                else: p.mkdir()
            with self.assertRaisesRegex(RuntimeError, 'STOP_DOCKER_BACKEND_UNCONFIGURED'):
                build_command(root/'out', prompt, image, 'compiled', workspace)

    def test_command_requires_explicit_image_and_ipc(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); prompt=root/'p'; image=root/'i'; workspace=root/'w'; ipc=root/'ipc'
            prompt.write_text('x'); image.write_text('x'); workspace.mkdir(); ipc.mkdir()
            values={'AGENT_INTERFACE_DOCKER_RUNNER':str(prompt),'AGENT_INTERFACE_DOCKER_SCHEMA':str(prompt),'AGENT_INTERFACE_DOCKER_INSTRUCTIONS':str(prompt),'AGENT_INTERFACE_DOCKER_IMAGE':'test:local','AGENT_INTERFACE_DOCKER_IPC':str(ipc)}
            old={k:os.environ.get(k) for k in values}
            os.environ.update(values)
            try:
                command=build_command(root/'out', prompt, image, 'compiled', workspace)
                self.assertIn('test:local', command)
                self.assertIn("HOST_MODEL_IPC_DIR=/ipc", command)
                self.assertIn('coordinate', command)
            finally:
                for k,v in old.items():
                    if v is None: os.environ.pop(k,None)
                    else: os.environ[k]=v

if __name__=='__main__': unittest.main()
