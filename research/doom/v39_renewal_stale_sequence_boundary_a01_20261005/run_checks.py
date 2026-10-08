import json, os, pathlib, subprocess, sys
root = pathlib.Path(__file__).resolve().parent
py = sys.executable
runs = {}
for mode, extra in (("normal", []), ("optimized", ["-O"])):
    env = os.environ.copy()
    env["V39_RENEWAL_TEST_MODE"] = mode
    command = [py, *extra, str(root / "test_current_main_boundary.py"), "-v"]
    completed = subprocess.run(command, cwd=root, env=env, text=True,
                               capture_output=True)
    (root / f"test_{mode}.stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (root / f"test_{mode}.stderr.txt").write_text(completed.stderr, encoding="utf-8")
    runs[mode] = {"command": command, "exit_code": completed.returncode,
                  "expected_exit_code": 0}
    if completed.returncode != 0:
        raise SystemExit(f"{mode} test failed\n{completed.stdout}\n{completed.stderr}")
    if not (root / f"observed_{mode}.json").is_file():
        raise SystemExit(f"{mode} run did not retain observed result")
compile_command = [py, "-m", "py_compile", str(root / "test_current_main_boundary.py"),
                   str(root / "baseline_map01_overlap_controller_v39.py"),
                   str(root / "baseline_doom_controller_failure_cleanup_v1.py")]
compiled = subprocess.run(compile_command, cwd=root, text=True, capture_output=True)
(root / "py_compile.stdout.txt").write_text(compiled.stdout, encoding="utf-8")
(root / "py_compile.stderr.txt").write_text(compiled.stderr, encoding="utf-8")
runs["py_compile"] = {"command": compile_command, "exit_code": compiled.returncode,
                       "expected_exit_code": 0}
if compiled.returncode:
    raise SystemExit(f"py_compile failed\n{compiled.stdout}\n{compiled.stderr}")
(root / "PROCESS_RESULTS.json").write_text(json.dumps(runs, indent=2) + "\n", encoding="utf-8")
print("PASS: exact current-main extracted renewal path + real failure cleanup in normal and -O; compilation passed")
