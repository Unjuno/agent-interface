"""Opt-in V15 release backend with an independently supervised input owner."""
from pathlib import Path

from doom_owner_thread_release_batch_backend_v1 import Backend as Previous
from input_owner_process_v1 import InputOwnerProcess


class Backend(Previous):
    """Keep the V15 telemetry contract while moving X ownership out of session."""

    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit, signal_readers)
        # The parent constructor creates an empty in-process owner. Close it
        # before any measured authority, then bind the process owner to the
        # exact X display selected by this session.
        self.owner.close()
        self.owner = InputOwnerProcess(
            session.name, Path(out) / "input-owner-process")
        try:
            emit({
                "event": "input_owner_process_ready",
                "schema": "input-owner-process-ready-v1",
                "owner_id": self.owner.owner_id,
                "service_pid": self.owner.service_pid,
                "display": session.name,
                "receipt_path": str(self.owner.receipt_path),
            })
        except BaseException as emit_error:
            try:
                self.owner.close()
            except BaseException as close_error:
                raise BaseExceptionGroup(
                    "owner readiness publication and cleanup both failed",
                    [emit_error, close_error],
                )
            raise

    def close(self):
        return self.owner.close()
