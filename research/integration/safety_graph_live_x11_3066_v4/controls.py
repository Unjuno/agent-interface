"""Synthetic corruption controls; never imports or invokes the X11 runtime."""
from __future__ import annotations

from audit import ALLOCATION, score


def row(config: str) -> dict:
    deadline = 1_000_000_000
    observed = deadline - 5_000_000
    started = observed + 100_000
    finished = deadline + 5_000_000
    return {
        "allocation": ALLOCATION,
        "config": config,
        "schedule": "cleanup_failure",
        "worker_returncode": 0,
        "worker_start_receipt": {"authority_deadline_ns": deadline, "authority_lease_ms": 150},
        "worker_receipt": {"dispatch_result": {"result": {
            "status": "execution_failed", "error": "BACKEND_EXECUTION_FAILED", "recovery_required": True,
        }}},
        "recovery_receipt_observed_ns": observed,
        "supervisor_attempt_count": 1,
        "supervisor_release": {
            "started_ns": started,
            "finished_ns": finished,
            "release": {"verified": True, "keys_down": [], "buttons_down": []},
        },
        "terminal_key_down": False,
        "post_cleanup_key_down": False,
        "keymap_transitions": [
            {"kind": "initial", "down": False, "observed_ns": deadline - 30_000_000},
            {"kind": "transition", "down": True, "observed_ns": deadline - 20_000_000},
            {"kind": "transition", "down": False, "observed_ns": deadline + 10_000_000},
        ],
    }


def rejected(name: str, mutate) -> None:
    candidate = [row("bare"), row("openbox")]
    mutate(candidate)
    if score(candidate)["decision"] == "PASS_EARLY_SUPERVISOR_RECOVERY_SCOPED":
        raise AssertionError(f"corruption control accepted: {name}")


def main() -> int:
    clean = [row("bare"), row("openbox")]
    assert score(clean)["decision"] == "PASS_EARLY_SUPERVISOR_RECOVERY_SCOPED"
    controls = [
        ("typed_recovery_false", lambda x: x[0]["worker_receipt"]["dispatch_result"]["result"].update(recovery_required=False)),
        ("duplicate_supervisor", lambda x: x[0].update(supervisor_attempt_count=2)),
        ("supervisor_too_late", lambda x: x[0]["supervisor_release"].update(finished_ns=1_050_000_001)),
        ("independent_keymap_too_late", lambda x: x[0]["keymap_transitions"][-1].update(observed_ns=1_050_000_001)),
        ("release_unverified", lambda x: x[0]["supervisor_release"]["release"].update(verified=False)),
        ("input_still_down", lambda x: x[0].update(terminal_key_down=True)),
        ("missing_keymap_release", lambda x: x[0].update(keymap_transitions=x[0]["keymap_transitions"][:-1])),
        ("wrong_allocation", lambda x: x[0].update(allocation="different")),
    ]
    for name, mutate in controls:
        rejected(name, mutate)
    late = [row("bare"), row("openbox")]
    late[0]["supervisor_release"]["finished_ns"] = 1_050_000_001
    assert score(late)["decision"] == "FAIL_EARLY_SUPERVISOR_RECOVERY"
    incomplete = [row("bare"), row("openbox")]
    incomplete[0]["keymap_transitions"] = incomplete[0]["keymap_transitions"][:-1]
    assert score(incomplete)["decision"] == "HOLD_RECOVERY_EVIDENCE_INCOMPLETE"
    construction = [row("bare"), row("openbox")]
    construction[0]["construction_only"] = True
    assert score(construction)["decision"] == "HOLD_CONSTRUCTION_ROWS_NOT_FORMAL"
    duplicate = [row("bare"), row("bare")]
    assert score(duplicate)["decision"] != "PASS_EARLY_SUPERVISOR_RECOVERY_SCOPED"
    print(f"PASS positive=1 corruption_controls={len(controls) + 2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
