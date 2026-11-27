"""Fake X only: characterize the selected admission boundary, never live input."""
import json
from pathlib import Path
import sys
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_map01_process_identity_backend import (
    backend_fixture, Backend, Executor, SignalReader, native,
)


def need(value, message):
    if not value:
        raise ValueError(message)


class AdmissionBoundaryStop(RuntimeError):
    pass


def cell(scope):
    with backend_fixture() as (original, events, generation, fake):
        # Alternate backends are constructed before the fault, so startup does
        # not accidentally introduce a second cleanup attempt during the stall.
        alternate = original
        if scope != "same-backend":
            session = original.session
            if scope == "new-session-same-display":
                session = SimpleNamespace(name=session.name, d=fake,
                                          context=session.context)
            out = original.out / scope
            out.mkdir()
            alternate = Backend(session, out, events.append,
                                {k: SignalReader(k) for k in ("health", "ammo")})
        original.snapshot("original-source", 0)
        if alternate is not original:
            alternate.snapshot("alternate-source", 0)
        entered, resume, terminal_ready = (threading.Event() for _ in range(3))
        sends = []
        original_send = native.xtest.fake_input.side_effect

        def send(connection, event, code):
            need(connection is fake, "unexpected native connection")
            sends.append({"event": event, "code": code,
                          "thread": threading.current_thread().name})
            if event == native.X.KeyRelease:
                entered.set()
                if not resume.wait(8):
                    raise RuntimeError("probe gate not resumed")
            return original_send(connection, event, code)

        def first_emit(row):
            events.append(row)
            if row.get("event") == "terminal":
                terminal_ready.set()

        admissions = []

        def stop_at_accept(row):
            admissions.append(row)
            if row.get("event") == "accepted":
                raise AdmissionBoundaryStop("probe stops before worker.start")

        first = Executor(original, first_emit)
        second = None
        try:
            with patch.object(native.xtest, "fake_input", side_effect=send):
                first.submit("held-original", [{"op": "hold", "keys": ["a"], "duration_ms": 5}],
                             original.sequence, time.perf_counter_ns() + 10_000_000_000)
                need(entered.wait(1), "original release send not entered")
                need(terminal_ready.wait(3), "original failure terminal missing")
                first.close()
                obligation = first.release_obligation_snapshot()
                need(obligation is not None and obligation["release"]["verified"] is False,
                     "original unverified custody missing")
                need(fake.down == {38}, "original key must still be held")
                before = len(sends)
                refusal = None
                try:
                    second = Executor(alternate, stop_at_accept)
                    second.submit("alternate-intent", [{"op": "hold", "keys": ["a"], "duration_ms": 5}],
                                  alternate.sequence, time.perf_counter_ns() + 1_000_000_000)
                except AdmissionBoundaryStop:
                    pass
                except ValueError as error:
                    refusal = str(error)
                accepted = [x for x in admissions if x.get("event") == "accepted"]
                need(len(sends) == before and fake.down == {38} and not resume.is_set(),
                     "alternate inspection changed input state")
                need(second is None or (second.active is not None and
                     second.active[2].ident is None), "alternate worker started")
                expected_refusal = scope == "same-backend"
                need(bool(accepted) is not expected_refusal, "unexpected admission boundary")
                need((refusal is not None) is expected_refusal, "unexpected refusal boundary")
                result = {
                    "case": scope,
                    "outcome": "RETAIN_SAME_BACKEND_FENCE" if expected_refusal else "FAIL_SHARED_INPUT_CUSTODY",
                    "original_closed": first.closed,
                    "original_obligation": obligation,
                    "original_custody": original.executor_custody_snapshot(),
                    "alternate_custody": alternate.executor_custody_snapshot(),
                    "same_backend": alternate is original,
                    "same_session": alternate.session is original.session,
                    "same_fake_server": True,
                    "target_process_digest": generation[0],
                    "accepted": accepted,
                    "refusal": refusal,
                    "alternate_worker_started": False,
                    "alternate_input_emissions": len(sends) - before,
                    "fake_keys_down_at_decision": sorted(fake.down),
                    "native_gate_resumed_at_decision": resume.is_set(),
                    "send_attempts_at_decision": list(sends),
                }
                resume.set()
                need(original.owner._inner.stopped.wait(1), "original owner did not retire")
                need(fake.down == set(), "fake release did not eventually complete")
                result["fake_keys_down_after_gate_resumed"] = sorted(fake.down)
                result["original_obligation_after_late_return"] = first.release_obligation_snapshot()
                print(json.dumps(result), flush=True)
                return result
        finally:
            resume.set()
            if second is not None:
                second.close()
            first.close()
            if alternate is not original:
                alternate.close()


if __name__ == "__main__":
    cases = [cell(scope) for scope in (
        "same-backend", "same-session-new-backend", "new-session-same-display")]
    print(json.dumps({"probe_status": "COMPLETE_CHARACTERIZATION",
                      "scientific_disposition": "FAIL_SHARED_INPUT_CUSTODY",
                      "cases": len(cases), "new_live_allocations": 0,
                      "scope": "One Python process/shared Fake X server; admission stopped by probe callback before alternate worker start; no second input, native timing or cross-process recovery claim."}), flush=True)
