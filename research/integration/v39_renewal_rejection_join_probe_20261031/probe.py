"""Execute the exact renewal rejection branch with a deliberately pending future."""
import ast, concurrent.futures, hashlib, json, threading, time
from pathlib import Path

source = Path(__file__).with_name("controller_source.py").read_bytes().replace(b"\r\n", b"\n")
assert hashlib.sha256(source).hexdigest() == "2fbb6587852b0853011a733e3d7b88a01175907698e9403cfd819062d946bab8"
tree = ast.parse(source)
matches = [n for n in ast.walk(tree) if isinstance(n, ast.If)
           and ast.unparse(n.test) == "next_accepted['event'] != 'accepted'"]
assert len(matches) == 1
branch = matches[0]
assert len(branch.body) == 1 and isinstance(branch.body[0], ast.Raise)
module = ast.fix_missing_locations(ast.Module(body=[branch], type_ignores=[]))
code = compile(module, "controller renewal rejection branch", "exec")
release = threading.Event()
started = threading.Event()
def pending():
    started.set()
    release.wait(timeout=2)
    return "retired"
timer = threading.Timer(.4, release.set)
timer.start()
start = time.monotonic()
try:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(pending)
        assert started.wait(timeout=1)
        try:
            exec(code, {"next_accepted": {"event":"rejected", "id":"cover-0-renew-1", "reason":"latest observation sequence required before input"}})
        finally:
            branch_exit_elapsed = time.monotonic() - start
except RuntimeError as error:
    catch_elapsed = time.monotonic() - start
    outcome = str(error)
finally:
    release.set()
    timer.join()
assert branch_exit_elapsed < .25
assert catch_elapsed >= .30
assert future.done()
print(json.dumps({"source_sha256":hashlib.sha256(source).hexdigest(), "branch_line":branch.lineno, "branch_exit_seconds":round(branch_exit_elapsed,3), "caught_after_seconds":round(catch_elapsed,3), "future_retired_before_outer_exception":future.done(), "rejection":outcome},indent=2))
