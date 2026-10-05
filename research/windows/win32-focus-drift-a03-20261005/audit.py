"""Independent raw/source audit for the bounded native foreground probe."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = HERE / "results" / "a03"
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition: bool, label: str, errors: list[str]) -> None:
    if not condition:
        errors.append(label)


def load(name: str):
    return json.loads((RUN / name).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    parent = FREEZE["parent_commit"]
    backend_path = "runtime/backends/win32_v1/backend.py"
    parent_blob = subprocess.run(
        ["git", "rev-parse", f"{parent}:{backend_path}"],
        cwd=REPO,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    check(parent_blob == FREEZE["parent_backend_blob"], "parent_backend_blob", errors)
    inventory = json.loads((HERE / "POSTRUN_SOURCE_INVENTORY.json").read_text(encoding="utf-8"))
    check(inventory["parent_commit"] == parent, "inventory_parent_commit", errors)
    for relative, expected_blob in inventory["parent_source_blobs"].items():
        actual_blob = subprocess.run(
            ["git", "rev-parse", f"{parent}:{relative}"],
            cwd=REPO,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        check(actual_blob == expected_blob, f"parent_source_blob:{relative}", errors)

    for relative, expected in FREEZE["candidate_sources"].items():
        check(sha256(REPO / relative) == expected, f"candidate_source:{relative}", errors)
    candidate_blobs = json.loads(
        (HERE / "POSTRUN_CANDIDATE_GIT_BLOBS.json").read_text(encoding="utf-8")
    )["sources"]
    for relative, identity in candidate_blobs.items():
        working = (REPO / relative).read_bytes()
        normalized = working.replace(b"\r\n", b"\n")
        staged = subprocess.run(
            ["git", "show", f":{relative}"],
            cwd=REPO,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        blob = subprocess.run(
            ["git", "rev-parse", f":{relative}"],
            cwd=REPO,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        check(hashlib.sha256(working).hexdigest() == identity["working_sha256"],
              f"candidate_working_sha256:{relative}", errors)
        check(hashlib.sha256(normalized).hexdigest() == identity["normalized_sha256"],
              f"candidate_normalized_sha256:{relative}", errors)
        check(normalized == staged, f"candidate_normalized_equals_staged:{relative}", errors)
        check(blob == identity["git_blob"], f"candidate_git_blob:{relative}", errors)

    baseline = load("baseline.raw.json")
    candidate = load("candidate.raw.json")
    check(baseline["target_hwnd"] != baseline["decoy_hwnd"], "baseline_distinct_hwnds", errors)
    check(candidate["target_hwnd"] != candidate["decoy_hwnd"], "candidate_distinct_hwnds", errors)
    check(baseline["foreground_switch"] == [{
        "message_posted": True, "foreground": baseline["decoy_hwnd"]
    }], "baseline_native_switch", errors)
    check(candidate["foreground_switch"] == [{
        "message_posted": True, "foreground": candidate["decoy_hwnd"]
    }], "candidate_native_switch", errors)

    baseline_reply = baseline["reply"]
    check(baseline["sendinput_calls"] == ["called"], "baseline_reached_input_boundary", errors)
    check(baseline_reply["status"] == "execution_failed", "baseline_refusal_status", errors)
    check("SendInput failed" in baseline_reply.get("detail", ""), "baseline_sentinel_failure", errors)
    check(baseline_reply.get("release", {}).get("verified") is True, "baseline_release_verified", errors)

    candidate_reply = candidate["reply"]
    check(candidate["sendinput_calls"] == [], "candidate_no_input_call", errors)
    check(candidate_reply["status"] == "execution_failed", "candidate_refusal_status", errors)
    check("foreground focus changed" in candidate_reply.get("detail", ""), "candidate_focus_mismatch", errors)
    check(candidate_reply.get("release", {}).get("verified") is True, "candidate_release_verified", errors)
    check(candidate_reply.get("release", {}).get("keys_down") == [], "candidate_no_keys_down", errors)
    check(candidate_reply.get("release", {}).get("buttons_down") == [], "candidate_no_buttons_down", errors)
    check(candidate_reply.get("input_transitions") == [], "candidate_no_transitions", errors)

    for prefix, expected_exit, success_token in (
        ("baseline", 1, "FAILED"),
        ("candidate", 0, "OK"),
    ):
        exit_text = (RUN / f"{prefix}.exit.txt").read_text(encoding="utf-8").strip()
        stdout = (RUN / f"{prefix}.stdout.txt").read_text(encoding="utf-8")
        check(exit_text == str(expected_exit), f"{prefix}_exit", errors)
        check(success_token in stdout, f"{prefix}_unittest_output", errors)

    for prefix, row in (("baseline", baseline), ("candidate", candidate)):
        check(row["target_effect_exists"] is False, f"{prefix}_no_target_effect", errors)
        check(row["decoy_effect_exists"] is False, f"{prefix}_no_decoy_effect", errors)

    files = (
        "FREEZE.json",
        "README.md",
        "RESULT.md",
        "POSTRUN_SOURCE_INVENTORY.json",
        "POSTRUN_CANDIDATE_GIT_BLOBS.json",
        "audit.py",
        "prepare_baseline.py",
        "results/a03/baseline.raw.json",
        "results/a03/baseline.stdout.txt",
        "results/a03/baseline.exit.txt",
        "results/a03/candidate.raw.json",
        "results/a03/candidate.stdout.txt",
        "results/a03/candidate.exit.txt",
    )
    result = {
        "schema": "win32-native-focus-drift-result-v1",
        "allocation": FREEZE["protocol"],
        "status": "PASS_NATIVE_FOREGROUND_REFUSAL" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "baseline_sendinput_calls": baseline["sendinput_calls"],
        "candidate_sendinput_calls": candidate["sendinput_calls"],
        "os_input_emitted": False,
        "application_effect_observed": False,
        "residual": "No proof of SendInput delivery, physical state, natural focus churn, task effect, or atomicity between foreground sampling and insertion.",
        "sha256": {name: sha256(HERE / name) for name in files},
        "raw_sha256": {
            "baseline": sha256(RUN / "baseline.raw.json"),
            "candidate": sha256(RUN / "candidate.raw.json"),
        },
    }
    (RUN / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])
    if errors:
        for error in errors:
            print(f"ERROR {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
