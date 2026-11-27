"""Remove local path tails from retained P09 exports and hash each edit."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN = ROOT / "run"
PATH_TAIL = re.compile(r"<private-path>(?:\\{1,8}[^\\\"<>|\r\n]+)*")
ABSOLUTE_PATH = re.compile(r"(?i)[A-Z]:\\{1,4}[^\"<>|\r\n]*")
rows = []
for path in sorted(RUN.rglob("*")):
    if not path.is_file() or "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
        continue
    before = path.read_bytes()
    try:
        text = before.decode("utf-8")
    except UnicodeDecodeError:
        continue
    after_text, count = ABSOLUTE_PATH.subn("<private-path>", text)
    after_text, count_tail = PATH_TAIL.subn("<private-path>", after_text)
    count += count_tail
    if after_text != text:
        after = after_text.encode("utf-8")
        path.write_bytes(after)
        rows.append({"path":path.relative_to(ROOT).as_posix(),
          "before_sha256":hashlib.sha256(before).hexdigest(),
          "after_sha256":hashlib.sha256(after).hexdigest(),"replacement_count":count})
report = {"schema":"agent-interface/p09-posthoc-path-scrub-v1",
  "scope":"privacy-only sanitation of already-redacted exports; not a restoration of raw evidence",
  "files_changed":len(rows),"replacements":rows}
(ROOT / "SANITIZATION-POSTHOC.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
print(f"{len(rows)} files sanitized")
