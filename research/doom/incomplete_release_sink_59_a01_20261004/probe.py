"""One-shot deterministic probe of incomplete release telemetry sink failures."""
import importlib.util
import json
import pathlib
import sys
import threading
import types


ROOT = pathlib.Path(__file__).resolve().parent
SOURCES = {
    "main": ROOT / "source_snapshots/main/doom_owner_thread_release_batch_backend_v1.py",
    "pr7635": ROOT / "source_snapshots/pr7635/doom_owner_thread_release_batch_backend_v1.py",
}


def load_backend(label, source):
    typed = types.ModuleType("doom_typed_release_backend_v2")

    class Previous:
        pass

    typed.Backend = Previous
    typed.suite = object()
    owner = types.ModuleType("input_transition_owner_v4")
    owner.InputOwner = object
    sys.modules["doom_typed_release_backend_v2"] = typed
    sys.modules["input_transition_owner_v4"] = owner
    spec = importlib.util.spec_from_file_location("tested_backend_" + label, source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Backend


def run_case(backend_type, accepts_before_raise):
    attempts = []
    delivered = []

    def emit(row):
        attempts.append(dict(row))
        if row["release_batch_position"] == 1:
            if accepts_before_raise:
                delivered.append(dict(row))
            raise OSError("injected sink failure at residual position 1")
        delivered.append(dict(row))

    backend = backend_type.__new__(backend_type)
    backend._release_batch = threading.local()
    backend.emit = emit
    context = {
        "rows": [
            {"event": "input_release_transition", "key": key,
             "release_batch_position": position}
            for position, key in enumerate(("a", "b", "c"))
        ],
        "identifier": "synthetic-program",
        "step": 4,
    }
    error = RuntimeError("original step failure")
    backend._finish_incomplete_release_batch(context, error, "step_exception")
    return {
        "sink_accept_before_raise": accepts_before_raise,
        "attempt_positions": [row["release_batch_position"] for row in attempts],
        "attempt_rows": attempts,
        "delivered_positions": [row["release_batch_position"] for row in delivered],
        "original_error_type": type(error).__name__,
        "original_error_text": str(error),
        "publication_metadata": getattr(error, "release_batch_publication", None),
        "context_rows_after": context["rows"],
        "error_notes": getattr(error, "__notes__", []),
    }


def main():
    rows = []
    for label, source in SOURCES.items():
        backend = load_backend(label, source)
        for accepts in (False, True):
            rows.append({
                "source": label,
                "source_sha256": __import__("hashlib").sha256(source.read_bytes()).hexdigest(),
                **run_case(backend, accepts),
            })
    print(json.dumps({"schema": "incomplete-release-publication-probe-v1",
                      "cases": rows}, sort_keys=True))


if __name__ == "__main__":
    main()
