"""Execute the exact frozen #8328 schedule once, each case on a fresh Xvfb."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import select
import signal
import socket
import subprocess
import sys
import time


STUDY_ID = "caps-text-query-xtest-a01-20261007"
STUDY = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def network_snapshot() -> dict:
    own = Path("/proc/self/ns/net").stat().st_ino
    init = Path("/proc/1/ns/net").stat().st_ino
    routes4 = [r for r in Path("/proc/net/route").read_text().splitlines()[1:]
               if r.split() and r.split()[0] != "lo"]
    routes6 = [r for r in Path("/proc/net/ipv6_route").read_text().splitlines()
               if r.split() and r.split()[-1] != "lo"]
    up = []
    for _, name in socket.if_nameindex():
        if name != "lo" and int(Path("/sys/class/net", name, "flags").read_text(), 16) & 1:
            up.append(name)
    result = {"namespace_inode": own, "pid1_namespace_inode": init,
              "ipv4_non_loopback_routes": routes4,
              "ipv6_non_loopback_routes": routes6,
              "up_non_loopback_interfaces": up,
              "interfaces": socket.if_nameindex()}
    if own == init or routes4 or routes6 or up:
        raise RuntimeError("not in a dedicated route-free network namespace")
    return result


def expected_schedule(freeze: dict) -> list[dict]:
    allocation = freeze["allocation"]
    arms = allocation["fixed_order"]
    ids = allocation["case_ids"]
    if len(ids) != allocation["total_cases"] or len(arms) != allocation["cases_per_block"]:
        raise ValueError("frozen allocation is internally inconsistent")
    rows = []
    for index, case_id in enumerate(ids):
        rows.append({"case_id": case_id, "arm": arms[index % len(arms)],
                     "block": index // len(arms) + 1})
    return rows


def verify_inputs(repo: Path, freeze: dict, manifest: dict, freeze_commit: str) -> None:
    if os.geteuid() != 0:
        raise RuntimeError("formal runner must execute as root inside the isolated VM")
    current_head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    if current_head != freeze_commit:
        raise RuntimeError("checkout differs from frozen execution commit")
    subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor",
                    manifest["current_main_ref"], current_head], check=True)
    if subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"], text=True):
        raise RuntimeError("source checkout is not clean before allocation")
    for rel, expected in manifest["files"].items():
        actual = digest(repo / rel)
        if actual != expected:
            raise RuntimeError(f"frozen file digest mismatch: {rel}")
    for rel, expected in manifest["runtime_closure"].items():
        if digest(repo / rel) != expected:
            raise RuntimeError(f"current-main runtime closure mismatch: {rel}")
    if digest(repo / freeze["source_base"]["backend_path"]) != freeze["source_base"]["backend_sha256"]:
        raise RuntimeError("current-main X11 backend differs from frozen source")


def environment_preflight(freeze: dict, out: Path) -> dict:
    import tkinter
    import Xlib
    from Xlib import display

    environment = freeze["environment"]
    expected = environment["installed"]
    python_version = ".".join(map(str, sys.version_info[:3]))
    xlib_version = ".".join(map(str, Xlib.__version__))
    tk_version = tkinter.Tcl().eval("info patchlevel")
    if python_version != expected["python"] or xlib_version != expected["python_xlib"] or tk_version != expected["tk"]:
        raise RuntimeError("Python, Python-Xlib, or Tk differs from the frozen environment")
    packages = {"xvfb": expected["xvfb"], "python3-xlib": expected["python_xlib"],
                "python3-tk": expected["python"], "libx11-dev": expected["libx11_dev"],
                "gcc": expected["gcc"], "git": expected["git"]}
    observed = {}
    for package, version_fragment in packages.items():
        version = subprocess.check_output(
            ["dpkg-query", "-W", "-f=${Version}", package], text=True
        ).strip()
        observed[package] = version
        if version_fragment not in version:
            raise RuntimeError(f"frozen package version mismatch: {package}={version}")
    if os.uname().machine not in ("aarch64", "arm64"):
        raise RuntimeError("formal VM architecture differs from frozen ARM64 environment")
    boundary = network_snapshot()
    check_dir = out / "preflight-xvfb"
    check_dir.mkdir()
    server, display_name, argv, stdout, stderr = start_xvfb(check_dir)
    try:
        connection = display.Display(display_name)
        xtest = connection.query_extension("XTEST")
        connection.close()
        if not xtest.present:
            raise RuntimeError("private Xvfb lacks the required XTEST extension")
    finally:
        code = stop_process(server)
        stdout.close()
        stderr.close()
    stderr_sha256 = digest(check_dir / "xvfb.stderr")
    expected_stderr_sha256 = environment["expected_xvfb_stderr_sha256"]
    result = {"study_id": STUDY_ID, "scope": "excluded pre-allocation readiness only",
              "network_boundary": boundary, "python": python_version,
              "python_xlib": xlib_version, "tk": tk_version,
              "platform": platform.platform(), "architecture": os.uname().machine,
              "packages": observed, "xvfb": {"pid": server.pid, "argv": argv,
              "display": display_name, "exit": code,
              "stdout": (check_dir / "xvfb.stdout").read_text(errors="replace"),
              "stderr": (check_dir / "xvfb.stderr").read_text(errors="replace"),
              "stderr_sha256": stderr_sha256,
              "socket_removed": not Path("/tmp/.X11-unix", "X" + display_name[1:]).exists(),
              "lock_removed": not Path("/tmp/.X" + display_name[1:] + "-lock").exists()},
              "xtest_present": True, "status": "PASS" if code == 0 else "STOP"}
    (out / "PREFLIGHT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if (code != 0 or stderr_sha256 != expected_stderr_sha256 or
            not result["xvfb"]["socket_removed"] or not result["xvfb"]["lock_removed"]):
        raise RuntimeError("pre-allocation Xvfb readiness/cleanup did not pass")
    return result


def start_xvfb(out: Path) -> tuple[subprocess.Popen, str, list[str], object, object]:
    stdout = (out / "xvfb.stdout").open("xb")
    stderr = (out / "xvfb.stderr").open("xb")
    read_fd, write_fd = os.pipe()
    argv = ["Xvfb", "-displayfd", str(write_fd), "-screen", "0", "640x240x24",
            "-nolisten", "tcp", "-ac"]
    proc = subprocess.Popen(argv, pass_fds=(write_fd,), stdout=stdout, stderr=stderr,
                            start_new_session=True)
    os.close(write_fd)
    try:
        ready, _, _ = select.select([read_fd], [], [], 10)
        if not ready:
            raise TimeoutError("Xvfb did not allocate a display")
        display_number = os.read(read_fd, 64).decode("ascii").strip()
        if not display_number.isdigit() or proc.poll() is not None:
            raise RuntimeError("Xvfb exited or returned an invalid display number")
        return proc, ":" + display_number, argv, stdout, stderr
    except Exception:
        stop_process(proc)
        stdout.close()
        stderr.close()
        raise
    finally:
        os.close(read_fd)


def stop_process(proc: subprocess.Popen) -> int:
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
    try:
        return proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        return proc.wait(timeout=5)


def execute_case(repo: Path, row: dict, case_dir: Path) -> dict:
    case_dir.mkdir()
    network = network_snapshot()
    server = None
    server_out = server_err = None
    started_ns = time.monotonic_ns()
    result = {"study_id": STUDY_ID, **row, "started_ns": started_ns,
              "network_boundary": network, "probe_exit": None,
              "xvfb_exit": None, "errors": [],
              "supervisor_pid": os.getpid(), "supervisor_argv": sys.argv}
    try:
        server, display_name, server_argv, server_out, server_err = start_xvfb(case_dir)
        result["xvfb"] = {"pid": server.pid, "argv": server_argv, "display": display_name}
        env = dict(os.environ, DISPLAY=display_name,
                   AGENT_INTERFACE_XVFB_PID=str(server.pid), PYTHONDONTWRITEBYTECODE="1")
        probe_argv = [sys.executable, "-B", str(STUDY / "public_dispatch_probe.py"),
                      "--repo", str(repo), "--out", str(case_dir / "probe"),
                      "--arm", row["arm"], "--mode", "formal", "--case-id", row["case_id"]]
        result["probe_argv"] = probe_argv
        result["probe_pid"] = None
        proc = subprocess.Popen(probe_argv, cwd=repo, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, start_new_session=True)
        result["probe_pid"] = proc.pid
        try:
            stdout, stderr = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            stdout, stderr = proc.communicate(timeout=5)
            result["errors"].append("probe timeout after 30s; process group killed")
            result["timed_out"] = True
        result["probe_exit"] = proc.returncode
        (case_dir / "probe.stdout").write_bytes(stdout)
        (case_dir / "probe.stderr").write_bytes(stderr)
        record_path = case_dir / "probe" / "record.json"
        result["record_exists"] = record_path.is_file()
        if record_path.is_file():
            result["record_sha256"] = digest(record_path)
            try:
                record = json.loads(record_path.read_text())
                result["record_display_server_pid"] = record.get("display_server", {}).get("pid")
                result["record_case_id"] = record.get("case_id")
            except (ValueError, UnicodeDecodeError) as exc:
                result["errors"].append(f"invalid probe record JSON: {exc}")
        else:
            result["errors"].append("probe emitted no record.json")
    except Exception as exc:
        result["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        if server is not None:
            result["xvfb_exit"] = stop_process(server)
        if server_out is not None:
            server_out.close()
        if server_err is not None:
            server_err.close()
        if "xvfb" in result:
            result["xvfb"]["stdout"] = (case_dir / "xvfb.stdout").read_text(errors="replace")
            result["xvfb"]["stderr"] = (case_dir / "xvfb.stderr").read_text(errors="replace")
            display_number = result["xvfb"]["display"][1:]
            result["xvfb"]["socket_removed"] = not Path("/tmp/.X11-unix", "X" + display_number).exists()
            result["xvfb"]["lock_removed"] = not Path("/tmp/.X" + display_number + "-lock").exists()
        result["ended_ns"] = time.monotonic_ns()
        (case_dir / "supervisor.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--freeze-commit", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    out = args.out.resolve()
    freeze_path = STUDY / "FREEZE.json"
    manifest_path = STUDY / "SOURCE_MANIFEST.json"
    freeze = json.loads(freeze_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    if freeze.get("status") != "FROZEN_NOT_STARTED":
        raise RuntimeError("formal status is not frozen-not-started")
    verify_inputs(repo, freeze, manifest, args.freeze_commit)
    if out.exists():
        raise FileExistsError(f"formal output path already exists: {out}")
    out.mkdir(parents=True)
    environment_preflight(freeze, out)
    schedule = expected_schedule(freeze)
    index = {"schema": "caps-text-query-xtest-formal-index-v1",
             "study_id": STUDY_ID, "source_freeze_commit": args.freeze_commit,
             "freeze_sha256": digest(freeze_path),
             "source_manifest_sha256": digest(manifest_path),
             "schedule": schedule, "cases": {}}
    (out / "RAW_INDEX.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    for row in schedule:
        case_dir = out / row["case_id"]
        summary = execute_case(repo, row, case_dir)
        index["cases"][row["case_id"]] = {
            "arm": row["arm"],
            "supervisor_sha256": digest(case_dir / "supervisor.json"),
            "record_sha256": summary.get("record_sha256"),
            "probe_exit": summary.get("probe_exit"),
            "xvfb_exit": summary.get("xvfb_exit"),
        }
        failures = []
        if summary.get("probe_exit") != 0:
            failures.append("probe exit")
        if summary.get("xvfb_exit") != 0:
            failures.append("Xvfb exit")
        supervisor = json.loads((case_dir / "supervisor.json").read_text())
        if supervisor.get("errors"):
            failures.extend(supervisor["errors"])
        xvfb = supervisor.get("xvfb", {})
        expected_xvfb_stderr = freeze["environment"]["expected_xvfb_stderr_sha256"]
        if digest(case_dir / "xvfb.stderr") != expected_xvfb_stderr:
            failures.append("unexpected Xvfb stderr")
        if (not xvfb.get("socket_removed") or not xvfb.get("lock_removed") or
                xvfb.get("pid") != supervisor.get("record_display_server_pid")):
            failures.append("Xvfb cleanup or process identity")
        if (case_dir / "probe.stderr").read_text(errors="replace"):
            failures.append("probe stderr")
        record_path = case_dir / "probe" / "record.json"
        if not record_path.is_file():
            failures.append("missing raw record")
        else:
            try:
                from audit_formal import audit_record
                raw_record = json.loads(record_path.read_text())
                failures.extend(audit_record(row["case_id"], row["arm"], raw_record))
            except (ValueError, UnicodeDecodeError, KeyError, TypeError) as exc:
                failures.append(f"raw record unreadable/incomplete: {type(exc).__name__}: {exc}")
        if failures:
            index["status"] = "STOP_AFTER_FIRST_UNEXPECTED_CASE"
            index["stopped_at"] = row["case_id"]
            index["case_errors"] = failures
        (out / "RAW_INDEX.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
        if failures:
            break
    errors = [case_id for case_id, item in index["cases"].items()
              if item["probe_exit"] != 0 or item["xvfb_exit"] != 0 or not item["record_sha256"]]
    if "status" not in index:
        index["status"] = "COMPLETE" if not errors and len(index["cases"]) == len(schedule) else "INCOMPLETE"
        index["case_errors"] = errors
    index["completed_ns"] = time.monotonic_ns()
    (out / "RAW_INDEX.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": index["status"], "cases": len(index["cases"]),
                      "errors": errors, "output": str(out)}, sort_keys=True))
    return 0 if index["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
