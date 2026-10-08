"""Raw-only broker outcome auditor; imports no runner or protocol helpers."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
import sys

EXPECTED = ("exit-0", "exit-23", "timeout-after-start", "missing-executable",
            "malformed-json", "idle-once", "sorted-once")
CORRUPTION_CONTROL_COUNT = 17


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def expected_docker_commands(receipt: dict, freeze: dict) -> tuple[list[str], list[str]]:
    formal = freeze["formal_invocation"]
    audit = freeze["audit_invocation"]
    image = freeze["source"]["image_id"]
    platform = freeze["source"]["platform"]
    limits = ["--network=none", "--read-only",
              f"--cpus={formal['cpu']}", f"--memory={formal['memory']}",
              f"--pids-limit={formal['pids_limit']}",
              "--cap-drop=" + ",".join(formal["cap_drop"]),
              "--security-opt=" + ",".join(formal["security_opt"])]
    common = ["docker", "--context", "desktop-linux", "run", "--rm",
              "--pull=never", "--platform", platform, *limits,
              "--tmpfs", formal["tmpfs"]]
    formal_command = [
        *common,
        "--mount", f"type=bind,src={receipt['resolved_repo']},dst=/src,readonly",
        "--mount", f"type=bind,src={receipt['resolved_study']},dst=/study,readonly",
        "--mount", f"type=bind,src={receipt['resource_release']},dst=/resource-release.json,readonly",
        "--mount", f"type=bind,src={receipt['resolved_receipt']},dst=/invocation-receipt.json,readonly",
        "--mount", f"type=bind,src={receipt['resolved_output']},dst=/out",
        "-e", "EXPECTED_BROKER_SHA256=" + freeze["source"]["broker_raw_sha256"],
        image, "python", "/study/runner.py",
    ]
    audit_limits = ["--network=none", "--read-only",
                    f"--cpus={audit.get('cpu', formal['cpu'])}",
                    f"--memory={audit.get('memory', formal['memory'])}",
                    f"--pids-limit={audit.get('pids_limit', formal['pids_limit'])}",
                    "--cap-drop=" + ",".join(audit.get("cap_drop", formal["cap_drop"])),
                    "--security-opt=" + ",".join(audit.get("security_opt", formal["security_opt"]))]
    audit_command = [
        "docker", "--context", "desktop-linux", "run", "--rm", "--pull=never",
        "--platform", platform, *audit_limits,
        "--mount", f"type=bind,src={receipt['resolved_study']},dst=/study,readonly",
        "--mount", f"type=bind,src={receipt['resolved_output']},dst=/out,readonly",
        "--mount", f"type=bind,src={receipt['resolved_audit_output']},dst=/audit-output",
        image, "python", "/study/audit.py",
    ]
    return formal_command, audit_command


def validate_invocation_receipt(receipt: dict, freeze: dict) -> None:
    formal = freeze["formal_invocation"]
    audit = freeze["audit_invocation"]
    require(formal.get("count") == 1 and formal.get("network") == "none" and
            formal.get("rootfs") == "read-only" and
            formal.get("source_mount") == "read-only" and
            formal.get("output_mount") == "fresh writable host-only directory" and
            formal.get("cpu") == 0.25 and formal.get("memory") == "256m" and
            formal.get("pids_limit") == 32 and formal.get("cap_drop") == ["ALL"] and
            formal.get("security_opt") == ["no-new-privileges:true"] and
            formal.get("tmpfs") == "/tmp:rw,exec,nosuid,size=16m" and
            formal.get("pull") == "never",
            "frozen formal resource contract is invalid")
    require(audit.get("count") == 1 and audit.get("network") == "none" and
            audit.get("rootfs") == "read-only" and
            audit.get("audit_source") == "read-only" and
            audit.get("raw_input") == "read-only" and
            audit.get("audit_report") == "separate fresh writable directory" and
            audit.get("corruption_controls") == CORRUPTION_CONTROL_COUNT,
            "frozen audit resource contract is invalid")
    require(isinstance(receipt, dict), "invocation receipt is not an object")
    require(receipt.get("allocation") == freeze.get("allocation"), "receipt allocation mismatch")
    require(receipt.get("issue") == freeze.get("issue"), "receipt issue mismatch")
    require(receipt.get("base_main") == freeze.get("base_main"), "receipt main mismatch")
    commit = receipt.get("source_commit_sha")
    require(isinstance(commit, str) and len(commit) == 40 and
            all(ch in "0123456789abcdef" for ch in commit), "receipt source commit invalid")
    source = freeze["source"]
    require(receipt.get("broker_git_blob") == source["broker_git_blob"],
            "receipt broker Git blob mismatch")
    require(receipt.get("broker_sha256") == source["broker_raw_sha256"],
            "receipt broker SHA-256 mismatch")
    require(receipt.get("image") == source["image_id"] + " " + source["platform"],
            "receipt image/platform mismatch")
    require(receipt.get("formal_source_sha256") == source.get("sha256"),
            "receipt formal source hash map mismatch")
    for name, expected in source.get("sha256", {}).items():
        path = Path(__file__).with_name(name)
        require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == expected,
                "auditor source bundle hash mismatch: " + name)
    for key in ("resolved_repo", "resolved_study", "resolved_output",
                "resolved_audit_output", "resolved_receipt", "resource_release"):
        require(isinstance(receipt.get(key), str) and receipt[key],
                "receipt path missing: " + key)
    require(receipt.get("docker_inventory_before") == [], "receipt Docker inventory was not empty")
    ownership = receipt.get("ownership_release")
    require(isinstance(ownership, dict) and ownership.get("issue") == freeze["issue"] and
            ownership.get("released") is True and
            ownership.get("observed_running_containers") == [],
            "receipt shared-resource release invalid")
    expected_formal, expected_audit = expected_docker_commands(receipt, freeze)
    require(receipt.get("command") == expected_formal,
            "formal invocation command/resource contract mismatch")
    require(receipt.get("audit_command_template") == expected_audit,
            "audit invocation command/resource contract mismatch")


def validate_receipt_binding(raw_receipt: dict, disk_receipt: dict, freeze: dict,
                             manifest: dict, actual_manifest: dict) -> None:
    require(manifest == actual_manifest, "complete output manifest mismatch")
    require(raw_receipt == disk_receipt,
            "raw invocation receipt differs from retained receipt bytes")
    validate_invocation_receipt(raw_receipt, freeze)


def reconcile_case_files(row: dict, case_root: Path) -> None:
    call_path = case_root / "child-calls.jsonl"
    disk_calls = ([json.loads(line) for line in call_path.read_text(encoding="utf-8").splitlines()]
                  if call_path.is_file() else [])
    require(row.get("child_calls") == disk_calls, row.get("name", "case") + " child-call bytes mismatch")
    disk_receipts = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((case_root / "ipc").glob("*.broker.json"))
    }
    require(row.get("receipts") == disk_receipts,
            row.get("name", "case") + " receipt bytes mismatch")
    disk_responses = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted((case_root / "ipc").glob("*.response.jsonl"))
    }
    require(row.get("responses") == disk_responses,
            row.get("name", "case") + " response bytes mismatch")
    if row.get("name") == "timeout-after-start":
        require(row.get("child_start_record") == (disk_calls[0] if len(disk_calls) == 1 else None),
                "timeout child-start record differs from call-log bytes")


def inspect(raw: dict, verify_files: bool = True,
            verify_queued_file: bool = True) -> list[str]:
    errors = []
    freeze = json.loads(Path(__file__).with_name("FREEZE.json").read_text(encoding="utf-8"))
    receipt = raw.get("invocation_receipt")
    if not verify_files:
        validate_invocation_receipt(receipt, freeze)
    rows = raw.get("cases")
    require(isinstance(rows, list) and len(rows) == 7, "case count")
    require(tuple(row.get("name") for row in rows) == EXPECTED, "case order/names")
    by_name = {row["name"]: row for row in rows}
    for row in rows:
        for name, meta in row.get("files", {}).items():
            if not verify_files:
                continue
            candidate = Path("/out") / name
            require(candidate.is_file(), "missing raw file: " + name)
            data = candidate.read_bytes()
            require(hashlib.sha256(data).hexdigest() == meta.get("sha256"),
                    "raw file digest: " + name)
            require(len(data) == meta.get("bytes"), "raw file length: " + name)
        if verify_files:
            reconcile_case_files(row, Path("/out/cases") / row["name"])

    if verify_files:
        manifest = json.loads(Path("/out/manifest.json").read_text(encoding="utf-8"))
        actual = {
            str(path.relative_to("/out")): {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            for path in sorted(Path("/out").rglob("*"))
            if path.is_file() and path.name != "manifest.json"
        }
        disk_receipt = json.loads(Path("/out/invocation-receipt.json").read_text(encoding="utf-8"))
        validate_receipt_binding(receipt, disk_receipt, freeze, manifest, actual)
        require(receipt.get("allocation") == raw.get("allocation"),
                "invocation receipt allocation mismatch")
        require(receipt.get("broker_sha256") == raw.get("broker_sha256"),
                "invocation receipt broker identity mismatch")
        require(receipt.get("broker_git_blob") == freeze["source"]["broker_git_blob"],
                "invocation receipt broker blob mismatch")

    for name, expected_exit in (("exit-0", 0), ("exit-23", 23)):
        row = by_name[name]
        require(row.get("process_exit") == expected_exit, name + " broker exit")
        receipt = row.get("receipts", {}).get(name + ".broker.json", {})
        require(receipt.get("returncode") == expected_exit, name + " child receipt")
        require(receipt.get("authority_granted") is False, name + " authority")
        require(len(row.get("child_calls", [])) == 1, name + " child calls")

    row = by_name["timeout-after-start"]
    receipt = row.get("receipts", {}).get("timeout-after-start.broker.json", {})
    require(row.get("child_start_marker") is True, "timeout marker absent")
    require(isinstance(row.get("child_start_marker_ns"), int), "timeout marker time")
    require(row.get("child_start_record", {}).get("event") == "child_started",
            "timeout start record")
    require(row.get("marker_error") is None, "timeout marker error")
    require(receipt.get("stop_reason") == "HOST_BROKER_SUBPROCESS_TIMEOUT",
            "timeout stop reason")
    require(receipt.get("returncode") is None, "timeout return code")
    require(row.get("responses", {}).get("timeout-after-start.response.jsonl") == "",
            "timeout response not empty")
    require(receipt.get("authority_granted") is False, "timeout authority")
    require(len(row.get("child_calls", [])) == 1, "timeout child start count")
    child_started_ns = row["child_start_record"].get("started_ns")
    broker_started_ns = receipt.get("started_ns")
    marker_observed_ns = row.get("child_start_marker_ns")
    timeout_s = row.get("broker_timeout_s")
    require(all(isinstance(v, int) for v in
                (child_started_ns, broker_started_ns, marker_observed_ns)),
            "timeout monotonic timestamps")
    receipt_timeout_s = receipt.get("timeout_s")
    require(isinstance(timeout_s, (int, float)) and math.isfinite(timeout_s),
            "timeout duration missing/nonfinite")
    require(isinstance(receipt_timeout_s, (int, float)) and
            math.isfinite(receipt_timeout_s), "receipt timeout duration missing/nonfinite")
    require(timeout_s == receipt_timeout_s == 5,
            "timeout duration differs from the frozen value")
    require(broker_started_ns <= child_started_ns <
            broker_started_ns + int(timeout_s * 1_000_000_000),
            "child start was not before broker deadline")
    require(child_started_ns <= marker_observed_ns <
            broker_started_ns + int(timeout_s * 1_000_000_000),
            "parent did not observe child marker before broker deadline")

    row = by_name["missing-executable"]
    receipt = row.get("receipts", {}).get("missing-executable.broker.json", {})
    require(receipt.get("stop_reason") == "HOST_BROKER_EXECUTABLE_UNAVAILABLE",
            "missing executable reason")
    require(receipt.get("authority_granted") is False, "missing authority")
    require(row.get("child_calls") == [], "missing executable invoked child")

    row = by_name["malformed-json"]
    require(row.get("child_calls") == [], "malformed request invoked child")
    require(row.get("receipts") == {}, "malformed request wrote receipt")
    require(row.get("responses") == {}, "malformed request wrote response")
    require(isinstance(row.get("process_exit"), int) and row["process_exit"] != 0,
            "malformed request did not fail nonzero")

    row = by_name["idle-once"]
    require(row.get("external_timeout") is True, "idle was not externally bounded")
    require(row.get("receipts") == {}, "idle wrote receipt")
    require(row.get("responses") == {}, "idle wrote response")

    row = by_name["sorted-once"]
    require(len(row.get("child_calls", [])) == 1, "sorted call count")
    require(row["child_calls"][0].get("stdin") == "prompt:a\n", "sorted first id")
    require(set(row.get("receipts", {})) == {"a.broker.json"}, "sorted receipt IDs")
    require(set(row.get("responses", {})) == {"a.response.jsonl"}, "sorted response IDs")
    require(row["receipts"]["a.broker.json"].get("authority_granted") is False,
            "sorted authority")
    if verify_queued_file:
        require((Path("/out/cases/sorted-once/ipc/z.request.json")).is_file(),
                "queued z request missing")
    return errors


def corruption_controls(raw: dict, verify_files: bool = True) -> int:
    mutations = (
        lambda x: x["cases"].pop(),
        lambda x: x["cases"][0].update(process_exit=1),
        lambda x: x["cases"][0]["receipts"]["exit-0.broker.json"].update(returncode=1),
        lambda x: x["cases"][2].update(child_start_marker=False),
        lambda x: x["cases"][2]["child_start_record"].update(started_ns=1),
        lambda x: x["cases"][2]["child_start_record"].update(started_ns=5_000_000_050),
        lambda x: x["cases"][6]["child_calls"][0].update(stdin="prompt:z\n"),
        lambda x: x["cases"][0]["receipts"]["exit-0.broker.json"].update(stderr="tampered"),
        lambda x: x["cases"][6]["responses"].update({"a.response.jsonl": "tampered"}),
        lambda x: x["cases"][2].update(broker_timeout_s=8),
        lambda x: x["cases"][2]["receipts"]["timeout-after-start.broker.json"].update(timeout_s=9),
        lambda x: x["cases"][5].update(external_timeout=False),
        lambda x: x["invocation_receipt"]["command"].__setitem__(8, "--network=host"),
        lambda x: x["invocation_receipt"]["command"].__setitem__(10, "--cpus=4"),
        lambda x: x["invocation_receipt"]["audit_command_template"].__setitem__(8, "--network=host"),
        lambda x: x["invocation_receipt"]["ownership_release"].update(released=False),
        lambda x: x["invocation_receipt"].update(docker_inventory_before=["unowned-container"]),
    )
    selected = mutations if verify_files else mutations[:7] + mutations[9:]
    rejected = 0
    for mutate in selected:
        candidate = copy.deepcopy(raw)
        mutate(candidate)
        try:
            inspect(candidate, verify_files=verify_files, verify_queued_file=False)
        except (ValueError, KeyError, TypeError, IndexError):
            rejected += 1
    expected = len(selected)
    require(rejected == expected, "corruption controls rejected " + str(rejected) + "/" + str(expected))
    if verify_files:
        require(rejected == CORRUPTION_CONTROL_COUNT,
                "formal corruption-control count differs from freeze")
    return rejected


def main() -> int:
    raw_path = Path("/out/raw.json")
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    errors = inspect(raw)
    rejected = corruption_controls(raw)
    report = {"status": "PASS_BROKER_BOUNDARY_SCOPED", "errors": errors,
              "corruption_controls": {"rejected": rejected, "total": CORRUPTION_CONTROL_COUNT}}
    (Path("/audit-output/audit.json")).write_text(
        json.dumps(report, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        report = {"status": "HOLD_EVIDENCE_INCOMPLETE", "errors": [
            type(exc).__name__ + ": " + str(exc)], "corruption_controls": None}
        destination = Path("/audit-output/audit.json")
        if destination.parent.is_dir():
            destination.write_text(json.dumps(report, sort_keys=True) + "\n",
                                   encoding="utf-8")
        print(json.dumps(report, sort_keys=True), file=sys.stderr)
        raise SystemExit(1)
