"""Private caller-owned Win32 image observation, without input authority."""
import copy, hashlib, io, pathlib, time, uuid
from PIL import Image
from runtime.guarded_x11_v1.history import ObservationHistory

class RetainedWin32Observation:

    def __init__(self, backend, target, out, capacity=2):
        self.backend = backend
        self.target = target
        self.out = pathlib.Path(out).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.scope = 'native-win32:' + uuid.uuid4().hex
        self.binding_revision = 0
        self.sequence = 0
        self.review_required = False
        self._history = ObservationHistory(capacity)
        self._initial = self._binding()

    def _binding(self):
        return {'surface': self.backend._target(self.target), 'geometry': copy.deepcopy(self.backend.geometry(self.target))}

    def observe(self, region):
        if self.review_required:
            raise ValueError('association review required')
        if type(region) is not list or len(region) != 4 or any((type(v) is not int for v in region)):
            raise ValueError('invalid region')
        x, y, w, h = region
        if min(x, y) < 0 or min(w, h) < 1 or w * h > 16777216:
            raise ValueError('invalid region')
        before = self._binding()
        if before != self._initial:
            self.review_required = True
            raise ValueError('association changed before capture')
        started = time.monotonic_ns()
        raw = self.backend.capture_pixels(self.target, 'window_client', x, y, w, h)
        finished = time.monotonic_ns()
        after = self._binding()
        if after != before:
            self.review_required = True
            raise ValueError('association changed during capture')
        if type(raw) is not bytes or len(raw) != w * h * 4:
            raise ValueError('invalid pixel payload')
        image = Image.frombytes('RGB', (w, h), raw, 'raw', 'BGRX')
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        encoded = buffer.getvalue()
        path = self.out / (uuid.uuid4().hex + '.png')
        with path.open('xb') as f:
            f.write(encoded)
        native = {'width': w, 'height': h, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'capture_started_ns': started, 'capture_finished_ns': finished, 'artifact': {'path': str(path), 'sha256': hashlib.sha256(encoded).hexdigest(), 'source_raw_sha256': hashlib.sha256(raw).hexdigest()}}
        sequence = self.sequence + 1
        observation = {'sequence': sequence, 'session_scope': self.scope, 'binding_revision': self.binding_revision, 'capture_ns': started, 'pointer_binding': before, 'region': list(region), 'native': native, 'input_dispatched': False, 'side_effect_authority': False}
        self._history[sequence] = (copy.deepcopy(observation), image)
        self.sequence = sequence
        return copy.deepcopy(observation)

    def get(self, sequence):
        observation, image = self._history[sequence]
        return (copy.deepcopy(observation), image.copy())
