import os
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from docker_model_call_backend_v1 import build_command

class DockerBackendTest(unittest.TestCase):
    def test_call_owns_prompt_creation_and_builder_owns_output_creation(self):
        source = Path(__file__).with_name('docker_model_call_backend_v1.py').read_text()
        self.assertEqual(source.count('root.mkdir(parents=True, exist_ok=False)'), 1)

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