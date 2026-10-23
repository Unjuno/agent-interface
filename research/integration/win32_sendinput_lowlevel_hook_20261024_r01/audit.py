"""Read-only, independent audit of the single frozen probe result."""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
EXPECTED = {
    "probe.py": "5c4496bd06a1f5c630db2f97339e398bf64fda03ec3c3ef67a1ae3414e3b1ea3",
    "conditions.json": "f50437a1ff21cf394a9cfaa7ee1169be35937515df415079e3aa5a0521e642b1",
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    raw_path = ROOT / "raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    hashes = {name: sha(ROOT / name) for name in EXPECTED}
    hashes["raw.json"] = sha(raw_path)
    no_source_drift = all(hashes[name] == value for name, value in EXPECTED.items())
    down = raw.get("send_down", {})
    up = raw.get("send_up", {})
    events = raw.get("events", [])
    downs = [e for e in events if e.get("kind") == "down"]
    ups = [e for e in events if e.get("kind") == "up"]
    callback_delay = downs[0].get("blocked_ns") if len(downs) == 1 else None
    checks = {
        "frozen_sources_unchanged": no_source_drift,
        "one_injected_down_callback": len(downs) == 1 and downs[0].get("vk") == 0x7C
            and bool(downs[0].get("flags", 0) & 0x10),
        "one_injected_up_callback": len(ups) == 1 and ups[0].get("vk") == 0x7C
            and bool(ups[0].get("flags", 0) & 0x10),
        "down_callback_delay_at_most_60ms": callback_delay is not None and callback_delay <= 60_000_000,
        "send_down_returned_after_callback": bool(downs) and downs[0].get("callback_exit_ns") is not None
            and down.get("entry_ns", 0) <= downs[0].get("callback_entry_ns", 0)
            and down.get("return_ns", 0) >= downs[0].get("callback_exit_ns", 0),
        "both_sendinput_calls_reported_one": down.get("sent") == 1 and up.get("sent") == 1,
        "final_f13_up": raw.get("final_f13", {}).get("down") is False,
        "no_runner_errors": raw.get("errors") == [],
        "hook_removed": raw.get("cleanup", {}).get("unhook_ok") is True,
        "hook_thread_exited": raw.get("cleanup", {}).get("thread_exited") is True,
    }
    disposition = "PASS" if all(checks.values()) else "FAIL"
    audit = {
        "packet": raw.get("packet"), "disposition": disposition,
        "method": "independent read-only JSON/timing/hash audit; no experiment re-execution",
        "hashes": hashes, "checks": checks,
        "measurements": {
            "callback_blocked_ns": callback_delay,
            "send_down_duration_ns": down.get("duration_ns"),
            "callback_exit_ns": downs[0].get("callback_exit_ns") if downs else None,
            "send_down_return_ns": down.get("return_ns"),
            "send_up_duration_ns": up.get("duration_ns"),
        },
        "interpretation": (
            "SendInput returned after the delayed low-level callback and a later UP was observed; "
            "the frozen callback-delay quality limit was exceeded, so the packet is FAIL. "
            "This single finite callback stall does not establish a hard release bound or "
            "recovery from an indefinitely blocked producer."
        ),
    }
    out = ROOT / "audit.json"
    with out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(audit, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(audit, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
