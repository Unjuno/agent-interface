import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

if len(sys.argv) == 3 and sys.argv[1] == "--worker":
    old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
    with open(sys.argv[2], "w", encoding="utf-8") as stream:
        json.dump({"verdict": "PASS_SCOPED_PIPE_NOTIFICATION"}, stream)
    os.kill(os.getpid(), signal.SIGINT)
    signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
    raise SystemExit("pending SIGINT was not delivered")

with tempfile.TemporaryDirectory(prefix="sigint-final-") as directory:
    summary = Path(directory) / "SUMMARY.json"
    child = subprocess.run([sys.executable, __file__, "--worker", str(summary)],
                          capture_output=True, text=True)
    with summary.open(encoding="utf-8") as stream:
        persisted = json.load(stream)
    print(json.dumps({"child_returncode": child.returncode,
                      "persisted_summary": persisted,
                      "child_stderr_has_keyboard_interrupt": "KeyboardInterrupt" in child.stderr},
                     sort_keys=True))
