"""Run A04 in normal and optimized Python, preserving the committed first outcome."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "run.py"


def prepare_output_dir(raw_path, package_dir=HERE):
    """Create a new output leaf outside the immutable evidence package."""
    output_dir = Path(raw_path).expanduser().resolve()
    package_dir = Path(package_dir).resolve()
    try:
        output_dir.relative_to(package_dir)
    except ValueError:
        pass
    else:
        raise ValueError("output directory must be outside the retained evidence package")
    try:
        output_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ValueError(f"output directory already exists: {output_dir}") from exc
    return output_dir


def run(label, options, output_dir):
    proc = subprocess.run(
        [sys.executable, *options, "-B", str(RUN)],
        cwd=HERE.parents[2],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    (output_dir / f"{label}.stdout.txt").write_bytes(proc.stdout)
    (output_dir / f"{label}.stderr.txt").write_bytes(proc.stderr)
    (output_dir / f"{label}.exit.txt").write_bytes(f"{proc.returncode}\n".encode("ascii"))
    if proc.returncode:
        raise SystemExit(f"{label} failed ({proc.returncode}); inspect {output_dir}")
    return proc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True,
                        help="new, nonexistent output directory outside this retained package")
    args = parser.parse_args(argv)
    try:
        output_dir = prepare_output_dir(args.output_dir)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    normal = run("normal", [], output_dir)
    optimized = run("optimized", ["-O"], output_dir)
    if normal.stdout != optimized.stdout or normal.stderr != optimized.stderr:
        raise SystemExit(f"normal and optimized outputs differ; inspect {output_dir}")
    result = json.loads(normal.stdout.decode("utf-8"))
    (output_dir / "RESULT.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: normal and optimized outputs are byte-identical; results: {output_dir}")
    print(normal.stdout.decode("utf-8"), end="")


if __name__ == "__main__":
    main()

