"""One-variable probe: drain late owner records after release_all returns."""
from bridge_v2_candidate import Backend as _Backend


class Backend(_Backend):
    def release_all(self):
        try:
            return super().release_all()
        finally:
            self._drain_owner_records()
