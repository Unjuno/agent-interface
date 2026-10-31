"""Capture-bound exact-region guard for one reviewed modal instance.

This helper does not find windows, establish review, mint references or issue
input. The caller supplies a trusted reference and regions, owns the session,
and must use verify_capture as an additional input dependency.
"""
import copy
import time


def _strict_equal(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(_strict_equal(left[key], right[key]) for key in left)
    if type(left) in (list, tuple):
        return len(left) == len(right) and all(_strict_equal(a, b) for a, b in zip(left, right))
    return left == right


class ReviewedModalGuard:
    def __init__(self, bridge, *, reference, regions, title, deadline_ns,
                 max_age_ns=1_500_000_000, clock=time.monotonic_ns):
        if (type(title) is not str or not title or type(deadline_ns) is not int or deadline_ns <= 0
                or type(max_age_ns) is not int or max_age_ns <= 0 or not callable(clock)):
            raise ValueError('explicit title, positive deadline and freshness required')
        try:
            width, height = reference.size
            if reference.mode != 'RGB' or type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
                raise ValueError('RGB reference required')
            if (type(regions) is not tuple or not regions or len(regions) > 64 or
                    any(type(box) is not tuple or len(box) != 4 or
                        any(type(v) is not int for v in box) or
                        not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height)
                        for box in regions)):
                raise ValueError('nonempty in-frame reviewed regions required')
            pixels = tuple(reference.crop(box).tobytes() for box in regions)
        except (AttributeError, TypeError, IndexError) as error:
            raise ValueError('valid RGB reference and regions required') from error
        self.bridge = bridge
        self.title = title
        self.deadline_ns = deadline_ns
        self.max_age_ns = max_age_ns
        self.clock = clock
        self.size = (width, height)
        self.regions = regions
        self.pixels = pixels
        self.snapshot = None

    def _valid(self, native, image, *, newer_than=0, binding=None, scope=None):
        try:
            b = self.bridge
            now = self.clock()
            if (type(now) is not int or type(native) is not dict or
                    type(native.get('sequence')) is not int or native['sequence'] <= newer_than or
                    native['sequence'] != b.sequence or type(native.get('capture_ns')) is not int or
                    not native['capture_ns'] <= now < min(self.deadline_ns, native['capture_ns'] + self.max_age_ns) or
                    type(native.get('binding_revision')) is not int or type(b.binding_revision) is not int or
                    native['binding_revision'] != b.binding_revision or
                    not _strict_equal(native.get('pointer_binding'), b._binding()) or
                    native['pointer_binding'].get('surface') != b.backend.targets[b.target].id or
                    native['native']['native_window_id'] != b.backend.targets[b.target].id or
                    b._focus_within_target() is not True or b._window_title() != self.title or
                    b.review_required is not False or b.session.recovery_required is not False or
                    (binding is not None and not _strict_equal(native['pointer_binding'], binding)) or
                    (scope is not None and b.scope != scope)):
                return False
            old, captured = b.history[native['sequence']]
            if (not _strict_equal(old, native) or image.mode != 'RGB' or captured.mode != 'RGB' or
                    image.size != self.size or captured.size != self.size or image.tobytes() != captured.tobytes()):
                return False
            return all(image.crop(box).tobytes() == pixels for box, pixels in zip(self.regions, self.pixels))
        except Exception:
            return False

    def arm(self, native, image):
        if self.snapshot is not None:
            raise ValueError('guard cannot be renewed')
        if getattr(self.bridge, 'active', None) is not None or not self._valid(native, image):
            raise ValueError('fresh reviewed modal association required')
        self.snapshot = {'sequence': native['sequence'], 'binding': copy.deepcopy(native['pointer_binding']),
                         'scope': self.bridge.scope}

    def verify_capture(self, native, image):
        if self.snapshot is None:
            return False
        return self._valid(native, image, newer_than=self.snapshot['sequence'],
                           binding=self.snapshot['binding'], scope=self.snapshot['scope'])
