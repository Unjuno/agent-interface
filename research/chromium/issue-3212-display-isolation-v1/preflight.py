"""Container preflight; deliberately does not claim a live Chromium effect."""
import json
import os
import shutil
import subprocess


def version(binary):
    try:
        return subprocess.run([binary, "--version"], text=True,
                              capture_output=True, check=False).stdout.strip()
    except OSError as exc:
        return f"error:{exc}"


def main():
    binaries = {name: shutil.which(name) for name in ("chromium", "Xvfb", "xdpyinfo")}
    result = {
        "network": "none",
        "binaries": binaries,
        "versions": {name: version(path) for name, path in binaries.items() if path},
        "display": os.environ.get("DISPLAY"),
        "formal_effect": False,
        "decision": "PREFLIGHT_ONLY" if all(binaries.values()) else "STOP_MISSING_RUNTIME",
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] == "PREFLIGHT_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
