"""Opt-in declared image predicate; caller retains semantic responsibility."""
import base64, copy, hashlib, json, os, sys
from .supervisor import run


def _worker_environment():
    """Make the current runtime package visible to the child interpreter."""
    origin = os.path.normcase(os.path.abspath(__file__))
    for entry in sys.path:
        if type(entry) is not str:
            continue
        root = os.getcwd() if not entry else os.path.abspath(entry)
        worker_module = os.path.normcase(os.path.join(root, 'runtime', 'guarded_win32_v1', 'worker_effect.py'))
        if origin == worker_module:
            env = os.environ.copy()
            inherited = env.get('PYTHONPATH')
            env['PYTHONPATH'] = os.pathsep.join([root, inherited] if inherited else [root])
            return env
    return None

class PixelEffect:

    def __init__(self, conditions, deadline_ns):
        self.conditions = copy.deepcopy(conditions)
        self.deadline = deadline_ns
        self.receipt = None

    def __call__(self, program, execution, row, image):
        if image.mode != 'RGB' or type(self.conditions) is not list or (not 1 <= len(self.conditions) <= 64):
            self.receipt = {'status': 'unknown', 'reason': 'invalid_condition', 'started': False}
            return None
        samples = []
        try:
            for condition in self.conditions:
                x, y = condition['point']
                rgb = condition['rgb']
                if type(x) is not int or type(y) is not int or (not (0 <= x < image.width and 0 <= y < image.height)):
                    raise ValueError('invalid point')
                if type(rgb) is not list or len(rgb) != 3 or any((type(v) is not int or not 0 <= v <= 255 for v in rgb)):
                    raise ValueError('invalid RGB')
                samples.append({'point': [x, y], 'rgb': list(image.getpixel((x, y)))})
        except Exception:
            self.receipt = {'status': 'unknown', 'reason': 'invalid_condition', 'started': False}
            return None
        sample_bytes = json.dumps(samples, separators=(',', ':'), sort_keys=True).encode()
        context = {'scope': row['session_scope'], 'sequence': row['sequence'], 'binding_revision': row['binding_revision'], 'artifact_sha256': row['native']['artifact']['sha256'], 'sample_sha256': hashlib.sha256(sample_bytes).hexdigest()}
        request = {'size': list(image.size), 'samples': samples, 'conditions': self.conditions, 'context': context}
        payload = json.dumps(request, separators=(',', ':')).encode()
        env = _worker_environment()
        if env is None:
            self.receipt = {'status': 'unknown', 'reason': 'runtime_path_unavailable', 'started': False}
            return None
        self.receipt = run([sys.executable, '-B', '-m', 'runtime.guarded_win32_v1.pixel_worker'], payload, self.deadline, env=env)
        self.receipt['payload_bytes'] = len(payload)
        if self.receipt['status'] != 'returned':
            return None
        result = json.loads(self.receipt['stdout'])
        if result.get('context') != context or type(result.get('task_success')) is not bool:
            return None
        return result['task_success']
