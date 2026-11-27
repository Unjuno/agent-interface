"""Independent raw-only method gate for the real InputOwner process probe."""


def audit(raw):
    errors = []
    session = raw.get("session", {})
    owner = raw.get("owner", {})
    observer = raw.get("observer", {})
    xvfb = raw.get("xvfb", {})
    release = owner.get("release_record")
    admitted = owner.get("admitted")

    if session.get("killed_by_sigkill") is not True or session.get("returncode") != -9:
        errors.append("session was not confirmed SIGKILLed")
    if owner.get("pid") == session.get("pid"):
        errors.append("InputOwner service shared session process")
    if owner.get("session_pid_at_start") != session.get("pid"):
        errors.append("InputOwner service was not spawned by session")
    if owner.get("ppid_at_eof") == session.get("pid"):
        errors.append("InputOwner service remained parented to killed session")
    if not (session.get("kill_requested_ns", 0) < owner.get("eof_ns", 0)
            < owner.get("close_started_ns", 0) <= owner.get("close_finished_ns", 0)):
        errors.append("session kill, owner EOF, and InputOwner close ordering invalid")
    if not isinstance(admitted, dict) or admitted.get("event") != "input_admission":
        errors.append("current InputOwner did not acknowledge key admission")
    if (not isinstance(admitted, dict) or admitted.get("key") != "a"
            or type(admitted.get("keycode")) is not int
            or admitted.get("valid_until_ns") is None):
        errors.append("admission receipt missing key identity or deadline")
    if owner.get("expected_focus", 0) <= 1:
        errors.append("observed focus identity missing")
    if (owner.get("intent_token") is None or not isinstance(release, dict)
            or release.get("intent_token") != owner.get("intent_token")
            or release.get("valid_until_ns") != admitted.get("valid_until_ns")):
        errors.append("release receipt intent/deadline mismatch")
    if (owner.get("release_record_count") != 1
            or not isinstance(release, dict)
            or release.get("event") != "owner_release"
            or release not in owner.get("owner_records", [])):
        errors.append("exactly one durable owner release record required")
    if (not isinstance(release, dict) or release.get("verified") is not True
            or release.get("keys_down") != []
            or release.get("buttons_down") != []
            or release.get("keys_unknown") != []
            or release.get("key_state_errors") != []):
        errors.append("InputOwner release record did not verify empty state")
    if not isinstance(release, dict) or release.get("reason") != "close":
        errors.append("recovery was not performed by InputOwner close")
    if owner.get("close_error") is not None:
        errors.append("InputOwner close returned an error")
    if owner.get("thread_stopped") is not True:
        errors.append("InputOwner thread did not stop")
    if owner.get("receipt_fsynced") is not True:
        errors.append("recovery receipt was not fsynced")
    if owner.get("returncode") != 0:
        errors.append("InputOwner service did not exit cleanly")
    if owner.get("forced_kill") is True:
        errors.append("InputOwner service required forced termination")
    if (observer.get("keymap_down_before_kill") is not True
            or observer.get("key_press_ns", 0) >= session.get("kill_requested_ns", 0)):
        errors.append("independent key-down before kill was not verified")
    if (observer.get("keymap_up_after_release") is not True
            or observer.get("key_release_ns", 0) < owner.get("close_started_ns", 0)):
        errors.append("independent KeyRelease/keymap-up was not verified")
    if xvfb.get("returncode") != 0:
        errors.append("Xvfb did not exit cleanly")
    return errors


if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    errors = audit(raw)
    result = {"decision": "PASS_METHOD_SCOPED" if not errors else "STOP",
              "checks": errors, "evidence_kind": "isolated production InputOwner process test"}
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(0 if not errors else 1)
