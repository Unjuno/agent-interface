"""Independent fail-closed audit for #3266 JSONL receipts."""
import json
import sys
from pathlib import Path


REQUIRED = {
    "allocation", "display", "profile", "launch_epoch_ns", "cdp_browser",
    "cdp_target", "chromium_pid", "xvfb_pid", "x11_windows", "dispatch",
    "dom_effect", "decision",
}
CONTROLS = {"stale_xid", "old_process", "positive_p2_effect"}


def main(path: str) -> int:
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    errors = []
    seen = set()
    for row in rows:
        control = row.get("control")
        seen.add(control)
        missing = sorted(REQUIRED - row.keys())
        if missing:
            errors.append(f"{control}: missing={missing}")
        correlated = (
            row.get("cdp_browser", {}).get("pid") == row.get("chromium_pid")
            and row.get("cdp_target", {}).get("display") == row.get("display")
            and row.get("cdp_target", {}).get("profile") == row.get("profile")
            and any(
                w.get("pid") == row.get("chromium_pid")
                and w.get("display") == row.get("display")
                for w in row.get("x11_windows", [])
            )
        )
        if control != "positive_p2_effect" and row.get("dispatch"):
            errors.append(f"{control}: forbidden dispatch")
        if row.get("dispatch") and not correlated:
            errors.append(f"{control}: dispatch without identity correlation")
        if row.get("dom_effect") and not row.get("dispatch"):
            errors.append(f"{control}: effect without dispatch")
        if control == "positive_p2_effect" and not (row.get("dispatch") and row.get("dom_effect") and correlated):
            errors.append("positive_p2_effect: missing correlated dispatch/effect")
    errors.extend(f"missing control={c}" for c in sorted(CONTROLS - seen))
    status = "PASS_AUDIT" if rows and not errors else "HOLD_AUDIT"
    print(f"{status} rows={len(rows)} controls={len(seen)} errors={len(errors)}")
    for error in errors:
        print(f"ERROR {error}")
    return 0 if status == "PASS_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
