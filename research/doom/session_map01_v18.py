"""Opt-in V15 session composition with a bounded tail after verified key-up.

The tail runs during final game cleanup, after V12 has closed the executor and
backend. It never changes controller-visible events or input authority. This
measurement path is not qualified for live efficacy claims.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import session_map01_v15 as previous
from map01_scorer_stdio_adapter_v2 import (
    MainThreadScorerStdin as StrictMainThreadScorerStdin,
    validate_release_receipt,
)

HERE = Path(__file__).resolve().parent
TAIL_DURATION_NS = 250_000_000
TAIL_MAX_SAMPLES = 8


def _verified_release(row):
    try:
        validate_release_receipt(row)
        return True
    except (TypeError, ValueError, AttributeError):
        return False


def _capture_backend(base_backend, release_holder):
    class CapturingReleaseBackend(base_backend):
        def __init__(self, session, out, emit, signal_readers):
            def capture_emit(row):
                emit(row)
                if _verified_release(row):
                    release_holder["latest"] = dict(row)

            super().__init__(session, out, capture_emit, signal_readers)

    return CapturingReleaseBackend


def run_tail_then_final_sample(polling, out, release_receipt, final_sample,
                               *, duration_ns=TAIL_DURATION_NS,
                               max_samples=TAIL_MAX_SAMPLES):
    """Record a bounded tail outcome, then always preserve V15's final sample."""
    outcome = {
        "schema": "map01-v18-post-release-tail-result-v1",
        "disposition": "CENSORED",
        "termination": "no_verified_release_receipt",
        "tail_samples": 0,
        "release_id": None,
        "release_step": None,
        "release_key": None,
        "controller_visible": False,
        "grants_input_authority": False,
    }
    try:
        if _verified_release(release_receipt):
            tail = polling.sample_tail(
                release_receipt=release_receipt,
                max_duration_ns=duration_ns,
                max_samples=max_samples,
            )
            outcome["termination"] = tail.get("termination", "unknown")
            outcome["disposition"] = tail.get("disposition", "CENSORED")
            outcome["tail_samples"] = tail.get("tail_samples", 0)
            outcome["release_id"] = tail.get("release_id")
            outcome["release_step"] = tail.get("release_step")
            outcome["release_key"] = tail.get("release_key")
            outcome["tail"] = tail
    except Exception as error:
        outcome["termination"] = "tail_error"
        outcome["error_type"] = type(error).__name__
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        (out / "scorer-post-release-tail.json").write_text(
            json.dumps(outcome, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    finally:
        final_sample()
    return outcome


def _record_source_manifest(out):
    path = Path(out) / "sources.json"
    if not path.is_file():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    for source in (HERE / "session_map01_v18.py",
                   HERE / "map01_scorer_stdio_adapter_v2.py",
                   HERE / "map01_overlap_controller_v39.py"):
        data[str(source.relative_to(HERE.parent))] = hashlib.sha256(source.read_bytes()).hexdigest()
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return True


def main():
    out = Path(previous._option("--out"))
    import doom_owner_thread_release_batch_backend_v1 as telemetry

    release_holder = {}
    original_backend = telemetry.Backend
    original_proxy = previous._GameProxy
    original_polling = previous.MainThreadScorerStdin
    polling_holder = {}

    def final_with_tail(final_sample):
        def run():
            polling = polling_holder["polling"]
            release_receipt = release_holder.get("latest")
            run_tail_then_final_sample(
                polling, out, release_receipt, final_sample)
        return run

    class TailGameProxy(original_proxy):
        def __init__(self, inner, final_sample):
            super().__init__(inner, final_with_tail(final_sample))

    def capturing_polling(stream, sample_fn, sample_sink, **kwargs):
        polling = StrictMainThreadScorerStdin(stream, sample_fn, sample_sink, **kwargs)
        polling_holder["polling"] = polling
        return polling

    telemetry.Backend = _capture_backend(original_backend, release_holder)
    previous._GameProxy = TailGameProxy
    previous.MainThreadScorerStdin = capturing_polling
    session_error = None
    try:
        return previous.main()
    except BaseException as error:
        session_error = error
        raise
    finally:
        telemetry.Backend = original_backend
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
