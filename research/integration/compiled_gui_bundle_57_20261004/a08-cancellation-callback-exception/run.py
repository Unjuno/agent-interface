"""Source-pinned test-double reproduction of cancellation-source exception."""

import hashlib
import importlib.util
import json
import sys
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
PR_COMMIT = "6144a1b0a2c88f5d88ff1fce148381f1f22269e1"
EXPECTED_ADAPTER_SHA256 = "43cd4e614de2cbb95b446b44314c15b5e9ccf711d9134dde8874a05774240e0d"
CORE_PATH = "runtime/core_v1/compiled_gui.py"
EXPECTED_CORE_SHA256 = "d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014"


def pinned_adapter_source():
    source = (Path(__file__).parent / "ADAPTER_PINNED.py").read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    if digest != EXPECTED_ADAPTER_SHA256:
        raise SystemExit(f"PR adapter source mismatch: {digest}")
    return source, digest


def load_adapter(source):
    # The callback/class code under test does not use Pillow. A stub lets this
    # narrow test load the exact file without installing image dependencies.
    resampling = type("Resampling", (), {"LANCZOS": 1})
    image_type = type("Image", (), {"Resampling": resampling, "LANCZOS": 1})

    pil = types.ModuleType("PIL")
    pil.Image = image_type
    sys.modules["PIL"] = pil
    module = types.ModuleType("pinned_pr7443_adapter")
    exec(compile(source, f"{PR_COMMIT}:ADAPTER_PINNED.py", "exec"), module.__dict__)
    return module


def main():
    from runtime.core_v1.compiled_gui import run as run_compiled

    core_digest = hashlib.sha256((ROOT / CORE_PATH).read_bytes()).hexdigest()
    if core_digest != EXPECTED_CORE_SHA256:
        raise SystemExit(f"compiled core source mismatch: {core_digest}")
    adapter_source, adapter_digest = pinned_adapter_source()
    adapter = load_adapter(adapter_source)
    execution = adapter.CompiledExecution.__new__(adapter.CompiledExecution)
    callback_checks = 0

    def cancelled():
        nonlocal callback_checks
        callback_checks += 1
        if callback_checks == 4:
            raise RuntimeError("cancellation source unavailable")
        return False

    execution._cancelled_source = cancelled
    interface = adapter.build_interface(
        {"field": "field-ref", "submit": "submit-ref"},
        "a08-private-test-double-v1",
    )
    observations = [
        {"exact_token_visible": False, "target_valid": True,
         "exact_saved_title": False},
        {"exact_token_visible": True, "target_valid": True,
         "exact_saved_title": False},
    ]
    sequence = 0
    actions, events = [], []

    def observe(_payload):
        nonlocal sequence
        sequence += 1
        return {
            "sequence": sequence, "captured_ns": time.perf_counter_ns(),
            "surface": "integrated-form", "predicates": observations[sequence - 1],
            "evidence_ref": f"frame-{sequence}",
            "evidence_digest": f"synthetic-frame-{sequence}",
        }

    def execute(payload):
        actions.append(payload["operation"])
        return {
            "status": "completed", "action_id": f"action-{len(actions)}",
            "effect_ref": f"effect-{len(actions)}",
            "release": {"verified": True, "keys_down": [], "buttons_down": []},
        }

    returned_receipt = None
    propagated_exception = None
    try:
        returned_receipt = run_compiled(interface, {
            "observe": observe,
            "admit": lambda payload: {
                "eligible": True, "status": "revalidated", "authorization": "one-use",
                "expected_sequence": payload["observation"]["sequence"],
                "valid_until_ns": time.perf_counter_ns() + 1_000_000_000,
            },
            "execute": execute,
            "verify_effect": lambda payload: {
                "status": "succeeded",
                "evidence_ref": payload["observation"]["evidence_ref"],
            },
            "cancelled": execution._cancelled,
            "journal": events.append,
        })
    except Exception as exc:  # capture the source-pinned behavior under test
        propagated_exception = f"{type(exc).__name__}: {exc}"

    terminals = [row for row in events if row["event"] == "action_terminal"]
    raw = {
        "schema": "compiled-form-cancel-callback-exception-a08-v1",
        "pr_source_commit": PR_COMMIT,
        "source_sha256": {
            "pr_adapter": adapter_digest,
            "compiled_core": core_digest,
            "runner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "callback_checks": callback_checks,
        "actions_dispatched": actions,
        "action_terminal_events": terminals,
        "journal_event_names": [row["event"] for row in events],
        "returned_receipt": returned_receipt,
        "propagated_exception": propagated_exception,
        "scope": "exact adapter callback + compiled core with test doubles; no GUI/OCR/provider/input/network",
    }
    Path(sys.argv[1]).write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n",
                                 encoding="utf-8")


if __name__ == "__main__":
    main()
