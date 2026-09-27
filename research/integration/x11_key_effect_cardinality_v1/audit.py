"""Raw-only auditor: no imports of controller, Xlib, Tk or the receiver."""
import hashlib
import json
from pathlib import Path
import sys

PATTERNS = {
    "NO_INPUT": [], "SINGLE_TAP": ["down", "up"],
    "DUPLICATE_DOWN": ["down", "down", "up"],
    "TWO_TAPS": ["down", "up", "down", "up"], "LONG_HOLD": ["down", "up"],
}
ORDER = list(PATTERNS)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_row(row, letter="a"):
    errors, gates = [], []
    checks = 0

    def check(ok, label, scientific=False):
        nonlocal checks
        checks += 1
        if not ok:
            (gates if scientific else errors).append(label)

    result = {}
    try:
        code = row["keycode"]
        window = row["ready"]["window"]
        mode = row["repeat"]
        schedule = row["schedule"]
        check(type(code) is int and 8 <= code < 256, "keycode")
        check(type(mode) is bool, "repeat type")
        check(row["letter"] == letter, "letter")
        check(row["disposition"] == "COMPLETE", "complete")
        check(row["receiver_exit"] == 0 and not row["receiver_stderr"], "child exit/stderr")
        check(row["ready"]["pid"] == row["receiver_pid"] != row["controller_pid"], "actor identity")
        check(row["ready"]["value"] == "" and row["ready"]["kind"] == "ready", "initial value")
        check(row["start_ns"] < row["end_ns"], "case clock")
        check(row["repeat_readback"]["global_mode"] == int(mode), "repeat mode readback")
        check(row["repeat_readback"]["led_mask"] == 0, "lock LEDs")
        repeat_bits = row["repeat_readback"]["auto_repeats"]
        check(len(repeat_bits) == 32 and repeat_bits[code//8] & (1 << (code%8)), "per-key repeat enabled")

        def state(s, expected_down=None, expect_focus=True):
            bitmap = s["keymap"]
            check(isinstance(bitmap, list) and len(bitmap) == 32 and
                  all(type(x) is int and 0 <= x < 256 for x in bitmap), "keymap type/length")
            check(row["start_ns"] <= s["start_ns"] <= s["end_ns"] <= row["end_ns"], "snapshot clock")
            check(s["buttons"] == 0, "pointer neutral")
            if expect_focus:
                check(s["focus"] == window, "snapshot focus")
            down = bool(bitmap[code//8] & (1 << (code%8)))
            if expected_down is not None:
                check(down == expected_down, "key state")
            remaining = bitmap.copy()
            remaining[code//8] &= ~(1 << (code%8))
            check(not any(remaining), "other keys neutral")
            return down

        state(row["initial"], False, False)
        state(row["focused"], False)
        state(row["terminal"], False)
        state(row["cleanup"], False, False)
        commands = row["commands"]
        check([r["kind"] for r in commands] == PATTERNS[schedule], "command sequence")
        was_down = False
        sampled_edges = 0
        last = row["focused"]["end_ns"]
        for command in commands:
            before = state(command["pre"], was_down)
            wanted = command["kind"] == "down"
            after = state(command["post"], wanted)
            check(last <= command["pre"]["start_ns"] <= command["pre"]["end_ns"] <=
                  command["call_start_ns"] <= command["call_end_ns"] <=
                  command["post"]["start_ns"], "command clock/order")
            if wanted and not before and after:
                sampled_edges += 1
            was_down = wanted
            last = command["post"]["end_ns"]
        check(last <= row["barrier"]["observed_ns"] <= row["terminal"]["start_ns"], "terminal barrier order")
        check(row["barrier"]["window"] == window and row["barrier"]["token"] == row["index"] + 1,
              "barrier identity")
        raw_events = [json.loads(s) for s in row["receiver_stdout"].splitlines()]
        check(raw_events == row["events"], "raw/decoded receiver equality")
        check(raw_events[0] == row["ready"], "ready line binding")
        check(raw_events[-1]["kind"] == "final", "final receipt")
        check(sum(e["kind"] == "final" for e in raw_events) == 1, "one final")
        check(all(e["pid"] == row["receiver_pid"] and e["window"] == window for e in raw_events),
              "receiver event identity")
        check(all(row["start_ns"] <= e["ns"] <= row["end_ns"] for e in raw_events), "receiver clocks")
        check([e["ns"] for e in raw_events] == sorted(e["ns"] for e in raw_events), "receiver event order")
        callbacks = raw_events[1:-1]
        check(all(e["kind"] in ("press", "release") for e in callbacks), "callback kind")
        press_count = 0
        release_count = 0
        for event in callbacks:
            check(event["keycode"] == code and event["keysym"] == letter, "callback key")
            if event["kind"] == "press":
                press_count += 1
                check(event["char"] == letter, "callback character")
            else:
                release_count += 1
            check(event["value"] == letter * press_count, "ordinary Entry effect progression")
        final = raw_events[-1]
        check(final["value"] == letter * press_count, "final exact value")
        check(final["callback_counts"] == {"press": press_count, "release": release_count}, "final counts")
        native = row["native"]
        check(all(e["window"] == window and e["keycode"] == code and
                  e["kind"] in ("press", "release") for e in native), "native key/window")
        check(all(row["start_ns"] <= e["observed_ns"] <= row["barrier"]["observed_ns"] for e in native),
              "native barrier coverage")
        # Native delivery times are uint32 X-server milliseconds; never subtract from monotonic ns.
        for kind in ("press", "release"):
            left = [(e["x_time"], e["state"]) for e in native if e["kind"] == kind]
            right = [(e["x_time"], e["state"]) for e in callbacks if e["kind"] == kind]
            if kind == "press":
                check(left == right, "native/Tk press identity/order")
            else:
                # Different X clients may expose different release projections.
                # Retain/count every native release; require ordered Tk inclusion.
                remaining = iter(left)
                included = all(any(native_event == tk_event for native_event in remaining)
                               for tk_event in right)
                check(included, "Tk release ordered native inclusion")
        expected_edges = 0 if schedule == "NO_INPUT" else 2 if schedule == "TWO_TAPS" else 1
        check(sampled_edges == expected_edges, "command-boundary state transitions", True)
        if schedule == "NO_INPUT":
            check(press_count == 0, "no-input positive", True)
        elif schedule == "TWO_TAPS":
            check(press_count == 2, "two tap effects", True)
        elif schedule == "SINGLE_TAP" or (schedule == "LONG_HOLD" and not mode):
            check(press_count == 1, "one effect control", True)
        elif schedule == "LONG_HOLD" and mode:
            check(press_count > 1, "repeat effect discriminator", True)
        result = dict(index=row["index"], rep=row["rep"], repeat=mode, schedule=schedule,
                      down_requests=sum(c["kind"] == "down" for c in commands),
                      sampled_down_transitions=sampled_edges, native_presses=sum(e["kind"] == "press" for e in native),
                      entry_characters=len(final["value"]),
                      native_releases=sum(e["kind"] == "release" for e in native),
                      tk_releases=release_count,
                      additional_native_releases=sum(e["kind"] == "release" for e in native)-release_count)
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        errors.append("invalid schema: " + repr(exc))
    return dict(checks=checks, errors=errors, gate_failures=gates, result=result)


def audit(root):
    errors, gates, rows, checks = [], [], [], 0
    freeze = json.loads((root / "FREEZE.json").read_text())
    sources = freeze["source_hashes"]
    for name, expected in sources.items():
        checks += 1
        if digest((root / name).read_bytes()) != expected:
            errors.append("source hash: " + name)
    process_ids = []
    raw_hashes = {}
    for b in range(2):
        folder = root / "formal" / f"batch-{b}"
        try:
            meta = json.loads((folder / "BATCH.json").read_text())
            start = json.loads((folder / "CONSUMED.json").read_text())
            receipt = json.loads((folder / "EXIT.json").read_text())
            expected_ids = list(range(b * 10, (b+1) * 10))
            conditions = {
                "batch complete": meta["disposition"] == "COMPLETE" and not meta["errors"],
                "fixed batch": meta["batch"] == b and not meta["construction"],
                "batch rows": meta["rows"] == expected_ids,
                "sources": meta["source_hashes"] == meta["source_hashes_after"] == sources,
                "consumption": start["source_hashes"] == sources and start["rows"] == [] and
                               start["runner_pid"] == meta["runner_pid"] and start["start_ns"] == meta["start_ns"],
                "actual outer exit": receipt["exit"] == 0 and receipt["timed_out"] is False,
                "outer actor": receipt["pid"] == meta["runner_pid"],
                "outer clock": receipt["start_ns"] <= meta["start_ns"] < meta["end_ns"] <= receipt["end_ns"],
                "actual server exit": meta["server_exit"] == 0 and meta["socket_absent"] is True,
                "repeat configuration": meta["repeat_rate"] == {"set_ok": 1, "get_ok": 1, "delay_ms": 250, "interval_ms": 50},
                "private server": "-nolisten" in meta["server_command"] and "tcp" in meta["server_command"] and "-auth" in meta["server_command"],
                "row-file denominator": len(list(folder.glob("case-*/row.json"))) == 10,
                "runner stderr": (root / "formal" / f"batch-{b}.stderr").read_bytes() == b"",
            }
            for label, ok in conditions.items():
                checks += 1
                if not ok:
                    errors.append(f"batch{b}: {label}")
            process_ids.extend([meta["runner_pid"], meta["server_pid"]])
            for j in range(10):
                path = folder / f"case-{j:02}" / "row.json"
                data = path.read_bytes()
                raw_hashes[str(path.relative_to(root))] = digest(data)
                row = json.loads(data)
                expected = (b * 10 + j, b, bool((j//5+b)%2), ORDER[(j%5+b)%5])
                got = (row["index"], row["rep"], row["repeat"], row["schedule"])
                checks += 2
                if got != expected:
                    errors.append(f"case{b}:{j}: schedule/identity")
                if not(meta["start_ns"] <= row["start_ns"] < row["end_ns"] <= meta["end_ns"] and
                       row["controller_pid"] == meta["runner_pid"]):
                    errors.append(f"case{b}:{j}: process/clock")
                process_ids.append(row["receiver_pid"])
                report = verify_row(row)
                checks += report["checks"]
                errors.extend(f"case{b}:{j}: {s}" for s in report["errors"])
                gates.extend(f"case{b}:{j}: {s}" for s in report["gate_failures"])
                rows.append(report["result"])
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"batch{b}: missing/invalid evidence {exc!r}")
    checks += 1
    if len(set(process_ids)) != 24:
        errors.append("24 distinct runner/server/receiver process identities")
    status = "PASS_KEY_STATE_EFFECT_CARDINALITY_BOUNDARY_SCOPED"
    if errors or len(rows) != 20:
        status = "HOLD_EVIDENCE_INTEGRITY"
    elif gates:
        status = "FAIL_KEY_STATE_EFFECT_CARDINALITY"
    return dict(status=status, checks=checks, errors=errors, gate_failures=gates,
                complete_rows=len(rows), rows=rows, raw_hashes=raw_hashes,
                source_hashes=sources, formal_reruns=0,
                scope="Provided Linux/Xvfb/Tk fixture; command-boundary logical-state samples, not hardware or continuous-state history")


if __name__ == "__main__":
    report = audit(Path(sys.argv[1]).resolve())
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["status"].startswith("PASS_") else 1)
