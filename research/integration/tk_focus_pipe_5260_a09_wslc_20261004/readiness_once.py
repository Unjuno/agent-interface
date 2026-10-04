"""Single-thread Tk callback barrier; claims before reentrant GUI work."""


class ReadinessOnce:
    def __init__(self):
        self._state = "WAITING"

    def prepare(self, update, is_ready, retry, schedule):
        if self._state != "WAITING":
            return False
        self._state = "PREPARING"
        try:
            update()
            if not is_ready():
                self._state = "WAITING"
                retry()
                return False
            self._state = "SCHEDULED"
            schedule()
            return True
        except Exception:
            self._state = "FAILED"
            raise

    def finalize(self, callback):
        if self._state != "SCHEDULED":
            return False
        self._state = "FINALIZING"
        try:
            callback()
            self._state = "FINALIZED"
            return True
        except Exception:
            self._state = "FAILED"
            raise
