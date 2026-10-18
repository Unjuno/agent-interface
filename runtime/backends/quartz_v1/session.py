from __future__ import annotations
from typing import Any
from runtime.core_v1.contract import admit_program
from .backend import QuartzBackend, QuartzBackendError, QuartzExecutionError

class QuartzRuntimeSession:
    def __init__(self, backend: QuartzBackend):
        self.backend = backend
        # Sticky for this session owner. Observation/binding changes and a
        # later cleanup receipt are not an explicit recovery protocol.
        self.recovery_required = False

    def _record_release(self, releases: Any) -> bool:
        verified = isinstance(releases, list) and bool(releases) and all(
            isinstance(row, dict) and row.get("verified") is True
            and row.get("keys_down") == [] and row.get("buttons_down") == []
            and row.get("keys_unknown", []) == []
            and row.get("buttons_unknown", []) == []
            and row.get("errors", []) == [] for row in releases)
        self.recovery_required = self.recovery_required or not verified
        return verified

    def dispatch(self, program: dict[str, Any], *, current_observation_seq: int, current_binding_revision: int, now_ns: int | None = None) -> dict[str, Any]:
        if self.recovery_required:
            return {"status":"refused","error":"INPUT_RECOVERY_REQUIRED",
                    "recovery_required":True,"input_dispatched":False,
                    "required_capabilities":[],"backend_emissions":self.backend.emissions}
        now_ns = self.backend.monotonic_ns() if now_ns is None else now_ns
        admission = admit_program(program, self.backend.manifest(), now_ns=now_ns, current_observation_seq=current_observation_seq, current_binding_revision=current_binding_revision)
        if not admission.accepted:
            return {"status":"refused","error":admission.error,"required_capabilities":list(admission.required_capabilities),"backend_emissions":self.backend.emissions}
        try: self.backend.preflight(program)
        except QuartzBackendError as error:
            release=self.backend._release_after_failure()
            self._record_release([release])
            return {"status":"refused","error":"BACKEND_CONSTRAINT","detail":str(error),"required_capabilities":list(admission.required_capabilities),"backend_emissions":self.backend.emissions,"release":release,"recovery_required":self.recovery_required}
        try: result=self.backend.execute(program)
        except QuartzExecutionError as error:
            self._record_release(error.execution.get("releases", []))
            return {"status":"execution_failed","error":"BACKEND_EXECUTION","detail":str(error),"backend_emissions":self.backend.emissions,"execution":error.execution,"recovery_required":self.recovery_required}
        except QuartzBackendError as error:
            self.recovery_required = True
            return {"status":"execution_failed","error":"BACKEND_EXECUTION","detail":str(error),"backend_emissions":self.backend.emissions,"recovery_required":True}
        except Exception:
            self.recovery_required = True
            raise
        verified = self._record_release(result.get("releases", []) if isinstance(result, dict) else [])
        return {"status":"completed" if verified else "release_unverified","admission":"accepted","required_capabilities":list(admission.required_capabilities),"execution":result,"recovery_required":self.recovery_required}
