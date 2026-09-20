import os
import json
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from docker_model_call_backend_v1 import build_command, call

class DockerBackendTest(unittest.TestCase):
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
