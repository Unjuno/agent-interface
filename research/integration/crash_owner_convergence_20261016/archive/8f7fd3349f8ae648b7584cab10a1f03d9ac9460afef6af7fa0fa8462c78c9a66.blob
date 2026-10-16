"""Strict PASS gate for the isolated session-parent crash recovery probe."""


def audit(raw):
    errors = []
    session = raw.get("session", {})
    owner = raw.get("owner", {})
    observer = raw.get("observer", {})
    xvfb = raw.get("xvfb", {})

    if session.get("killed_by_sigkill") is not True or session.get("returncode") != -9:
        errors.append("session was not confirmed SIGKILLed")
    if not isinstance(session.get("dead_ns"), int):
        errors.append("session death time missing")
    if owner.get("pid") == session.get("pid"):
        errors.append("owner shared session process")
    if owner.get("session_pid_at_start") != session.get("pid"):
        errors.append("owner was not spawned by session")
    if owner.get("ppid_at_eof") == session.get("pid"):
        errors.append("owner remained parented to dead session")
    # EOF is the causal boundary: this dedicated stream is held only by the
    # session, so EOF follows its death. The controller's wait() return is a
    # later observation and may be timestamped after the owner's release.
    if not (session.get("kill_requested_ns", 0) < owner.get("eof_ns", 0)
            < owner.get("release_started_ns", 0)):
        errors.append("session kill, owner EOF, and release ordering invalid")
    if not owner.get("keys_down_before_release"):
        errors.append("owner had no held key to recover")
    if owner.get("keys_down_after_release"):
        errors.append("owner retained held keys after release")
    if owner.get("keymap_up") is not True:
        errors.append("owner did not verify keymap-up")
    if owner.get("receipt_fsynced") is not True:
        errors.append("recovery receipt was not fsynced")
    if owner.get("returncode") != 0:
        errors.append("owner did not exit cleanly")
    if owner.get("forced_kill") is True:
        errors.append("owner required forced termination")
    if not (session.get("kill_requested_ns", 0) > observer.get("key_press_ns", 0)
            and observer.get("keymap_down_before_kill") is True):
        errors.append("key-down before session kill was not independently verified")
    if observer.get("key_release_ns", 0) < owner.get("release_started_ns", 0):
        errors.append("independent KeyRelease missing or preceded owner release")
    if observer.get("keymap_up_after_release") is not True:
        errors.append("independent keymap did not verify key-up")
    if xvfb.get("returncode") != 0:
        errors.append("Xvfb did not exit cleanly")
    return errors


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    path = Path(sys.argv[1])
    errors = audit(json.loads(path.read_text(encoding="utf-8")))
    result = {"decision": "PASS_METHOD_SCOPED" if not errors else "STOP",
              "checks": errors, "evidence_kind": "isolated process topology experiment"}
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(0 if not errors else 1)
