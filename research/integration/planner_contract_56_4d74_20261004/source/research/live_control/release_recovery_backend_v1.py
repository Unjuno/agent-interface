"""Actual passive recovery observation after owner release, before terminal."""
from cause_session_v1 import Backend as Previous, suite


class Backend(Previous):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); self._active_identity = None

    def execute(self, step, cancel, identifier, index):
        self._active_identity = (identifier, index)
        return super().execute(step, cancel, identifier, index)

    def release_all(self):
        release = super().release_all()
        cause = self.lease.interruption_snapshot() if hasattr(self, "lease") else None
        record = cause.get("record") if isinstance(cause, dict) else None
        if (release.get("verified") is True and isinstance(record, dict) and
                record.get("reason") in ("focus_changed", "surface_changed") and
                self._active_identity is not None):
            identifier, index = self._active_identity
            self.emit({"event": "post_release_observation_started", "id": identifier,
                       "step": index, "grants_input_authority": False})
            self.snapshot(identifier, index)
            self.emit({"event": "post_release_observation_complete", "id": identifier,
                       "step": index, "sequence": self.sequence,
                       "grants_input_authority": False})
        return release
