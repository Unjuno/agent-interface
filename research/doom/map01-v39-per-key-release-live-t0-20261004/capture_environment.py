"""Write an exact receipt for the dedicated isolated Linux guest runtime."""
import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path


def output(command):
    return subprocess.check_output(command, text=True).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = {
        "schema": "map01-v39-telemetry-runtime-environment-v1",
        "platform": platform.platform(),
        "python_version": sys.version,
        "python_executable": str(Path(sys.executable).resolve()),
        "uname": output(["uname", "-a"]),
        "os_release": Path("/etc/os-release").read_text(encoding="utf-8"),
        "dpkg_packages": output([
            "dpkg-query", "-W", "-f=${binary:Package}=${Version}\\n"]),
        "python_packages": output([str(args.python), "-m", "pip", "freeze", "--all"]),
        "network_isolation": "unshare -n applied to candidate and auditor",
        "allocation_id": "MAP01-V39-RELEASE-TELEMETRY-LIVE-59-T0-20261004-01",
        "orb_machine_id": "01M4283HRND5FW9AG9FXYX0B7H",
    }
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")


if __name__ == "__main__":
    main()
