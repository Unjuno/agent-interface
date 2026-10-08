"""Opt-in per-key measured-release scorer tail for construction review only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import session_map01_v15 as previous
from map01_scorer_stdio_adapter_v3 import (
    MainThreadScorerStdin as MeasuredScorerStdin,
    MeasuredReleaseError,
)

HERE = Path(__file__).resolve().parent
TAIL_DURATION_NS = 250_000_000
TAIL_MAX_SAMPLES = 8


def _capture_backend(base_backend, state):
    class CapturingPerKeyBackend(base_backend):
        def __init__(self, session, out, emit, signal_readers):
            self._v19_state = state

            def capture_emit(row):
                emit(row)
                if row.get("event") not in ("input_admission", "input_release_measurement"):
                    return
                state["backend"] = self
                if row.get("event") == "input_admission":
                    state["admission"] = dict(row)
                    state["candidate"] = None
                    return
                down = state.get("admission")
                if down is None or self.held:
                    state["candidate"] = None
                    return
                state["candidate"] = (dict(down), dict(row), list(self.held))

            super().__init__(session, out, capture_emit, signal_readers)
            state["backend"] = self

    return CapturingPerKeyBackend


def _run_measured_tail(polling, out, candidate, final_sample, *,
                       duration_ns=TAIL_DURATION_NS, max_samples=TAIL_MAX_SAMPLES):
    outcome = {
        "schema": "map01-v19-perkey-post-release-tail-result-v1",
        "disposition": "CENSORED", "termination": "no_verified_perkey_release",
        "tail_samples": 0, "controller_visible": False,
        "grants_input_authority": False,
    }
    try:
        if candidate is not None:
            down, up, held_after = candidate
            tail = polling.sample_measured_tail(
                admission_event=down, release_measurement=up,
                backend_held_after=held_after,
                max_duration_ns=duration_ns, max_samples=max_samples)
            outcome.update({
                "termination": tail.get("termination", "unknown"),
                "disposition": tail.get("disposition", "CENSORED"),
                "tail_samples": tail.get("tail_samples", 0),
                "tail": tail,
            })
    except MeasuredReleaseError as error:
        outcome.update({
            "termination": "no_matched_release_pair",
            "disposition": "CENSORED",
            "reason": str(error),
            "error_type": type(error).__name__,
        })
    except Exception as error:
        outcome["termination"] = "tail_error"
        outcome["error_type"] = type(error).__name__
    output = Path(out)
    output.mkdir(parents=True, exist_ok=True)
    try:
        (output / "scorer-post-release-tail.json").write_text(
            json.dumps(outcome, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    finally:
        final_sample()
    return outcome


def _record_source_manifest(out):
    path = Path(out) / "sources.json"
    if not path.is_file():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    for source in (HERE / "session_map01_v19.py",
                   HERE / "map01_scorer_stdio_adapter_v3.py",
                   HERE / "map01_scorer_stdio_adapter_v1.py",
                   HERE / "map01_v39_perkey_bridge_a01" / "bridge.py",
                   HERE / "map01_overlap_controller_v39.py"):
        data[str(source.relative_to(HERE.parent))] = hashlib.sha256(source.read_bytes()).hexdigest()
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return True


def main():
    out = Path(previous._option("--out"))
    import session_map01_v12 as session_module
    import doom_owner_thread_release_batch_backend_v1 as telemetry
    from map01_v39_perkey_bridge_a01.bridge import Backend as PerKeyBackend

    state = {}
    original_backend = session_module.Backend
    original_telemetry_backend = telemetry.Backend
    original_proxy = previous._GameProxy
    original_polling = previous.MainThreadScorerStdin
    polling_holder = {}

    def final_with_tail(final_sample):
        def run():
            _run_measured_tail(polling_holder["polling"], out,
                               state.get("candidate"), final_sample)
        return run

    class TailGameProxy(original_proxy):
        def __init__(self, inner, final_sample):
            super().__init__(inner, final_with_tail(final_sample))

    def capturing_polling(stream, sample_fn, sample_sink, **kwargs):
        polling = MeasuredScorerStdin(stream, sample_fn, sample_sink, **kwargs)
        polling_holder["polling"] = polling
        return polling

    telemetry.Backend = _capture_backend(PerKeyBackend, state)
    previous._GameProxy = TailGameProxy
    previous.MainThreadScorerStdin = capturing_polling
    session_error = None
    try:
        return previous.main()
    except BaseException as error:
        session_error = error
        raise
    finally:
        session_module.Backend = original_backend
        telemetry.Backend = original_telemetry_backend
        previous._GameProxy = original_proxy
        previous.MainThreadScorerStdin = original_polling
        try:
            _record_source_manifest(out)
        except BaseException as provenance_error:
            if session_error is not None:
                raise BaseExceptionGroup(
                    "session and source provenance finalization failed",
                    [session_error, provenance_error]) from None
            raise


if __name__ == "__main__":
    main()
