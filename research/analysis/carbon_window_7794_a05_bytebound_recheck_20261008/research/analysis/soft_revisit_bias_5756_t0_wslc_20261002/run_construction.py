from pathlib import Path
import subprocess
import sys


def main():
    memory_max = Path("/sys/fs/cgroup/memory.max").read_text(encoding="ascii").strip()
    print(f"cgroup_memory_max_bytes={memory_max}", flush=True)
    if memory_max != "536870912":
        print("STOP: expected the requested 512 MiB memory ceiling to be enforced", file=sys.stderr, flush=True)
        return 2
    result = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "-v", "test_policy", "test_audit"],
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
