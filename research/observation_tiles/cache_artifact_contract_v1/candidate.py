"""Research support-envelope wrappers; quiescent, cooperative PNG storage only."""
import hashlib
import io
from PIL import Image
from vendor.image_artifact import ImageArtifactSink

POLICIES = ('ORIGINAL', 'BYTE_PIN_REPAIR', 'PIXEL_CHECK_REPAIR')
LIMIT = 262144


class Candidate:
    def __init__(self, directory, policy):
        if policy not in POLICIES:
            raise ValueError('unknown policy')
        self.policy = policy
        self.sink = ImageArtifactSink(directory)
        self.pin = None

    def publish(self, frame):
        guard = 'NOT_NEEDED'
        same = self.sink.previous is not None and frame == self.sink.previous
        if same and self.policy != 'ORIGINAL':
            valid = False
            guard = 'INVALID_OR_MISSING'
            try:
                with self.sink.path.open('rb') as source:
                    raw = source.read(LIMIT + 1)
                if len(raw) > LIMIT:
                    raise ValueError('byte bound')
                if self.policy == 'BYTE_PIN_REPAIR':
                    valid = hashlib.sha256(raw).hexdigest() == self.pin
                else:
                    # Verify container integrity, then actually decode the same bytes.
                    with Image.open(io.BytesIO(raw), formats=['PNG']) as image:
                        if image.size != (frame.width, frame.height) or image.mode != frame.mode:
                            raise ValueError('geometry or mode')
                        image.verify()
                    with Image.open(io.BytesIO(raw), formats=['PNG']) as image:
                        image.load()
                        valid = image.tobytes() == frame.pixels
                guard = 'MATCH' if valid else 'MISMATCH'
            except (OSError, ValueError, SyntaxError):
                valid = False
            if not valid:
                # This instance belongs only to this wrapper. No upstream edits.
                self.sink.previous = None
        elif same:
            guard = 'ORIGINAL_EXISTENCE_ONLY'
        receipt = self.sink.publish(frame)
        if not receipt['image_reused']:
            self.pin = hashlib.sha256(self.sink.path.read_bytes()).hexdigest()
        return {'receipt': receipt, 'guard': guard,
                'authority': 'none', 'model_calls': 0, 'input_dispatched': False}
