"""Apply the prospective oracle-boundary change to a temporary A04 copy only."""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile


SOURCE_SHA256 = {
    "candidate.py": "e058cdc69700b5cb08bbda13cb90c83caca36e238edcddbd9fde5cfced76d1a4",
    "runner.py": "a301dcbc4650c7327d9ef31c11ed24d8d3815129394d7ea9c4603b4422184838",
    "auditor.py": "42515f709ab223e8c75f594b742dbde0e8e8d0adc20514b33fc1093c2182a778",
}

RUNNER_HELPER = '''def control_step(arm, yaw, pitch, step, image, reference_points, meta):
    """Evaluate one arm; privileged pose control must not require image features."""
    if arm == "viewstate_oracle":
        action = None if step >= 12 else (
            max(-0.08, min(0.08, -0.72 * yaw)),
            max(-0.08, min(0.08, -0.72 * pitch)),
        )
        return None, None, action
    pixels = image.split(bytes([10]) + b"255" + bytes([10]), 1)[1]
    points = candidate.detect(meta["width"], meta["height"], pixels)
    features = candidate.feature_vector(arm, points, reference_points)
    action = None if step >= 12 else candidate.choose_action(
        arm, points, reference_points, meta
    )
    return points, features, action
'''
RUNNER_OLD = '''          try:
           pts=candidate.detect(width,height,image.split(b"\\n255\\n",1)[1])
           fv=candidate.feature_vector(arm,pts,ref_xy)
           if step>=12: action=None
           elif arm=="viewstate_oracle": action=(max(-.08,min(.08,-.72*yaw)),max(-.08,min(.08,-.72*pitch)))
           else: action=candidate.choose_action(arm,pts,ref_xy,meta)
           status=("STEP_LIMIT" if step>=12 else "STOP") if action is None else "ACTION"
'''
RUNNER_NEW = '''          try:
           pts,fv,action=control_step(arm,yaw,pitch,step,image,ref_xy,meta)
           status=("STEP_LIMIT" if step>=12 else "STOP") if action is None else "ACTION"
'''
AUDITOR_HELPER = '''def audit_image_points(arm, width, height, pixels, status):
    """Reconstruct image features only for arms whose decisions use them."""
    if arm == "viewstate_oracle":
        return None
    try:
        return centers(width, height, pixels)
    except ValueError:
        if status != "YIELD":
            raise
        return None
'''
AUDITOR_OLD = '''        try: actual=centers(w,h,p)
        except ValueError:
            if r["status"]!="YIELD": raise
            actual=None
'''
AUDITOR_NEW = '''        actual=audit_image_points(truth["arm"],w,h,p,r["status"])
'''


def read_exact(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return stream.read()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"expected one frozen {label} anchor, found {count}")
    return source.replace(old, new, 1)


def write_exact(path: Path, source: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        stream.write(source)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_oracle_boundary_patch.py <temporary-A04-source-dir>")
    source_dir = Path(sys.argv[1]).resolve()
    temp_dir = Path(tempfile.gettempdir()).resolve()
    if source_dir != temp_dir and temp_dir not in source_dir.parents:
        raise SystemExit("refusing to patch outside the system temporary directory")

    for name, expected in SOURCE_SHA256.items():
        actual = hashlib.sha256((source_dir / name).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"refusing non-frozen {name}: SHA-256 {actual}")

    runner_path = source_dir / "runner.py"
    runner = read_exact(runner_path)
    runner = replace_once(
        runner,
        "def scenario(seed,condition):",
        RUNNER_HELPER + "\n\ndef scenario(seed,condition):",
        "runner insertion",
    )
    runner = replace_once(runner, RUNNER_OLD, RUNNER_NEW, "runner arm dispatch")

    auditor_path = source_dir / "auditor.py"
    auditor = read_exact(auditor_path)
    auditor = replace_once(
        auditor,
        "def expected_stress_yield(condition,arm,points,reference,meta):",
        AUDITOR_HELPER + "\n\ndef expected_stress_yield(condition,arm,points,reference,meta):",
        "auditor insertion",
    )
    auditor = replace_once(auditor, AUDITOR_OLD, AUDITOR_NEW, "auditor image dispatch")

    write_exact(runner_path, runner)
    write_exact(auditor_path, auditor)
    for name in ("runner.py", "auditor.py"):
        digest = hashlib.sha256((source_dir / name).read_bytes()).hexdigest()
        print(f"patched {name} sha256={digest}")


if __name__ == "__main__":
    main()
