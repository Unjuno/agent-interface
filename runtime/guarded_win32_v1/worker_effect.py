"""Opt-in declared image predicate; caller retains semantic responsibility."""
import base64, copy, hashlib, json, sys
from .supervisor import run

class PixelEffect:

    def __init__(self, conditions, deadline_ns):
        self.conditions = copy.deepcopy(conditions)
        self.deadline = deadline_ns
        self.receipt = None

    def __call__(self, program, execution, row, image):
        raw = image.convert('RGB').tobytes()
        context = {'scope': row['session_scope'], 'sequence': row['sequence'], 'binding_revision': row['binding_revision'], 'artifact_sha256': row['native']['artifact']['sha256'], 'rgb_sha256': hashlib.sha256(raw).hexdigest()}
        request = {'size': list(image.size), 'rgb': base64.b64encode(raw).decode(), 'conditions': self.conditions, 'context': context}
        payload = json.dumps(request, separators=(',', ':')).encode()
        self.receipt = run([sys.executable, '-B', '-m', 'runtime.guarded_win32_v1.pixel_worker'], payload, self.deadline)
        if self.receipt['status'] != 'returned':
            return None
        result = json.loads(self.receipt['stdout'])
        if result.get('context') != context or type(result.get('task_success')) is not bool:
            return None
        return result['task_success']
