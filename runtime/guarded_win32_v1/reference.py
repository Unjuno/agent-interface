import copy, time
from .retained import RetainedWin32Observation
from runtime.guarded_x11_v1.handles import TargetHandleStore

class ReferencedWin32Observation(RetainedWin32Observation):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = TargetHandleStore(self.scope)

    def _binding(self):
        binding = super()._binding()
        binding['focus'] = int(self.backend.user32.GetForegroundWindow() or 0)
        return binding

    def context(self, sequence):
        row, image = self.get(sequence)
        b = row['pointer_binding']
        g = b['geometry']
        if b['focus'] != b['surface']:
            raise ValueError('target not foreground')
        if row['region'] != [0, 0, g['width'], g['height']]:
            raise ValueError('reference requires full client observation')
        result = copy.deepcopy(row)
        result['pointer_binding'] = {'focus': b['focus'], 'surface': b['surface'], 'geometry': [g['x'], g['y'], g['width'], g['height']]}
        return (result, image)

    def mint(self, alias, sequence, box, now_ns=None):
        if self.review_required:
            raise ValueError('association review required')
        row, image = self.context(sequence)
        return self.store.mint(alias, 'window_content', box, row, image, time.monotonic_ns() if now_ns is None else now_ns, ttl_ms=1000, freshness_ms=1000)

    def resolve(self, alias, offset, sequence, now_ns=None, scope=None):
        if self.review_required:
            raise ValueError('association review required')
        row, image = self.context(sequence)
        return self.store.resolve_point(alias, offset, row, image, time.monotonic_ns() if now_ns is None else now_ns, session_scope=self.scope if scope is None else scope)
