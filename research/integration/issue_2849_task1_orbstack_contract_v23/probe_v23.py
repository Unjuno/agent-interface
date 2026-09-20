from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RUN = HERE / "evidence/seed-284923"
OUTER = "sha256:436172d89b145c6a9f9a57e655422c9558b3b0235347dd77607e9d61bcfa6393"
INNER = "sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073"
SOCKET = Path("/Users/taka/.orbstack/run/docker.sock")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    fixture = RUN / "fixture/payload.txt"
    expected = sha(fixture)
    outer_id = subprocess.check_output(
        ["docker", "--context", "orbstack", "image", "inspect", OUTER,
         "--format", "{{.Id}} {{.Architecture}}"], text=True, timeout=20).strip()
    inner_id = subprocess.check_output(
        ["docker", "--context", "orbstack", "image", "inspect", INNER,
         "--format", "{{.Id}} {{.Architecture}}"], text=True, timeout=20).strip()
    if outer_id != OUTER + " arm64" or inner_id != INNER + " arm64":
        raise RuntimeError("STOP_IMAGE_IDENTITY_MISMATCH")
    code = (
        "import json,os,subprocess; "
        "src=os.environ['PROBE_FIXTURE_HOST']; img=os.environ['PROBE_INNER_IMAGE']; "
        "cmd=['docker','run','--rm','--network','none','--mount',"
        "'type=bind,src='+src+',dst=/probe,readonly','--entrypoint','/bin/sh',"
        "img,'-lc','sha256sum /probe/payload.txt']; "
        "p=subprocess.run(cmd,text=True,capture_output=True,timeout=30); "
        "print(json.dumps({'command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}))"
    )
    outer_command = [
        "docker", "--context", "orbstack", "run", "--rm", "--network", "none",
        "--mount", f"type=bind,src={ROOT},dst={ROOT}",
        "--mount", f"type=bind,src={SOCKET},dst=/var/run/docker.sock",
        "-e", "DOCKER_HOST=unix:///var/run/docker.sock",
        "-e", "PROBE_FIXTURE_HOST=" + str(fixture.parent.resolve()),
        "-e", "PROBE_INNER_IMAGE=" + INNER,
        "--entrypoint", "python3", OUTER, "-c", code,
    ]
    frozen = {
        "issue": 2849, "seed": 284923, "preregistration_comment": 5752035338,
        "main_commit": subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip(),
        "probe_sha256": sha(Path(__file__)), "readme_sha256": sha(HERE / "README.md"),
        "fixture_sha256": expected, "outer_image": outer_id, "nested_image": inner_id,
        "authority_granted": False, "task_started": False, "model_calls": 0,
        "host_broker_started": False, "maximum_outer_invocations": 1,
        "maximum_nested_invocations": 1,
    }
    (RUN / "frozen-inputs.json").write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n")
    try:
        outer = subprocess.run(outer_command, cwd=ROOT, capture_output=True, text=True,
                               timeout=90, check=False)
        outer_rc, outer_out, outer_err = outer.returncode, outer.stdout, outer.stderr
    except subprocess.TimeoutExpired as exc:
        outer_rc, outer_out, outer_err = None, exc.stdout or "", exc.stderr or ""
    nested = None
    try:
        rows = [json.loads(line) for line in outer_out.splitlines() if line.startswith("{")]
        nested = rows[-1] if rows else None
    except (json.JSONDecodeError, IndexError):
        pass
    digest = None
    if nested and nested.get("returncode") == 0:
        digest = nested.get("stdout", "").split()[0] if nested.get("stdout", "").split() else None
    checks = {
        "pinned_outer_and_nested_images": outer_id == OUTER + " arm64" and inner_id == INNER + " arm64",
        "outer_and_nested_commands_network_disabled": "--network" in outer_command and "none" in outer_command
        and nested is not None and "--network" in nested.get("command", [])
        and nested["command"][nested["command"].index("--network") + 1] == "none",
        "nested_container_read_only_fixture_digest_exact": nested is not None
        and nested.get("returncode") == 0 and digest == expected,
        "outer_returned_zero": outer_rc == 0,
        "no_task_or_broker_or_model_activity": True,
    }
    result = {
        "issue": 2849, "seed": 284923,
        "status": "PASS_NESTED_BIND" if all(checks.values()) else "STOP_NESTED_BIND",
        "checks": checks, "expected_fixture_sha256": expected,
        "observed_fixture_sha256": digest, "outer_returncode": outer_rc,
        "outer_stdout": outer_out[-4000:], "outer_stderr": outer_err[-4000:],
        "nested_receipt": nested, "outer_invocations": 1,
        "nested_invocations": 1 if nested is not None else 0,
        "task_started": False, "host_broker_started": False,
        "model_calls": 0, "authority_granted": False,
    }
    (RUN / "probe-result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    files = sorted(path for path in RUN.rglob("*") if path.is_file() and path.name != "SHA256SUMS")
    (RUN / "SHA256SUMS").write_text("".join(
        f"{sha(path)}  {path.relative_to(RUN)}\n" for path in files))
    return 0 if result["status"] == "PASS_NESTED_BIND" else 1


if __name__ == "__main__":
    raise SystemExit(main())
