import re
from pathlib import Path


_IMAGE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]*@(sha256:[0-9a-f]{64})\Z")
_PLATFORM = "linux/arm64"
_WORKDIR_NAME = "owner_keyup_formal_x11_5156_20261001_07"
_ALLOCATION = "MAP01-OWNER-KEYUP-BRACKET-5156-ORB-20261001-07"
_FROZEN_MAIN = "40885011a5d8e15ab10bb6cc0e8eef65661718ee"
_IMAGE_REF = "agent-interface-2972@sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27"


def _validated_paths(workdir, results_dir, image, platform):
    image_match = _IMAGE.fullmatch(image) if isinstance(image, str) else None
    if image_match is None:
        raise ValueError("image must be a repository reference pinned by a full sha256 digest")
    if image != _IMAGE_REF:
        raise ValueError("image must match the frozen locally cached X11 candidate reference")
    if platform != _PLATFORM:
        raise ValueError(f"allocation requires platform {_PLATFORM}")

    workdir = Path(workdir)
    if not workdir.is_absolute():
        raise ValueError("workdir must be absolute")
    if (workdir.name != _WORKDIR_NAME or workdir.parent.name != "live_control"
            or workdir.parent.parent.name != "research"):
        raise ValueError("workdir must be this allocation's dedicated research directory")
    if not workdir.is_dir():
        raise ValueError("workdir must exist as a directory before launch")
    expected_results = workdir / "results" / "formal-01"
    results_dir = Path(results_dir)
    if not results_dir.is_absolute() or results_dir.resolve(strict=False) != expected_results.resolve(strict=False):
        raise ValueError("results directory must be this allocation's formal-01 output directory")
    if not results_dir.is_dir():
        raise ValueError("results directory must exist before bind mounting")
    return workdir.resolve(strict=False).as_posix(), results_dir.resolve(strict=False).as_posix(), image_match.group(1)


def _base_argv(source, results, image):
    return [
        "docker", "run", "--rm", "--pull=never", "--platform=linux/arm64",
        "--network", "none", "--cpus=1", "--memory=512m", "--pids-limit=64",
        "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
        "--cap-drop=ALL", "--security-opt=no-new-privileges",
        "--mount", f"type=bind,source={source},target=/src,readonly",
        "--mount", f"type=bind,source={results},target=/results",
        "--entrypoint", "/bin/sh", image,
    ]


def build_command(workdir, results_dir, image, platform):
    """Build, but never execute, the one-shot Docker argv for Allocation 07."""
    source, results, digest = _validated_paths(workdir, results_dir, image, platform)
    script = (
        'python3 -c "import Xlib; from Xlib import display"'
        " && command -v xvfb-run >/dev/null"
        f" && FORMAL_ALLOCATION={_ALLOCATION}"
        f" FORMAL_FROZEN_MAIN={_FROZEN_MAIN}"
        f" FORMAL_IMAGE_DIGEST={digest}"
        f" FORMAL_PLATFORM={_PLATFORM}"
        " FORMAL_V11_DIR=/src/dependencies"
        " exec xvfb-run -a python3 /src/run_formal_x11.py /results/raw.jsonl"
    )
    return _base_argv(source, results, image) + ["-ceu", script]


def build_audit_command(workdir, results_dir, image, platform):
    """Build the isolated audit argv; caller must gate it on successful runner exit."""
    source, results, _ = _validated_paths(workdir, results_dir, image, platform)
    script = "exec python3 /src/audit_formal_x11.py /results/raw.jsonl /src/EXPECTED.json /results/audit.json"
    return _base_argv(source, results, image) + ["-ceu", script]
