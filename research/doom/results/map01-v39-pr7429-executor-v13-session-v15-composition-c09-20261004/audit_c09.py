import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
errors = []
for item in manifest["files"]:
    path = root / item["path"]
    if not path.is_file():
        errors.append(f"missing:{item['path']}")
        continue
    data = path.read_bytes()
    if len(data) != item["bytes"]:
        errors.append(f"size:{item['path']}")
    if hashlib.sha256(data).hexdigest() != item["sha256"]:
        errors.append(f"sha256:{item['path']}")
expected = {
    "raw/01-order.txt": (1, "test_release_publication_finishes_before_terminal"),
    "raw/02-executor-v13.txt": (4, "Ran 4 tests"),
    "raw/03-cancel-release.txt": (6, "test_accept_then_raise_release_delivery_is_not_retried"),
    "raw/04-running-action-guard.txt": (4, "Ran 4 tests"),
    "raw/05-session-selection.txt": (1, "Ran 1 test"),
}
for name, (count, sentinel) in expected.items():
    path = root / name
    if not path.is_file():
        errors.append(f"missing-raw:{name}")
        continue
    text = path.read_text(encoding="utf-8-sig")
    if "EXIT=0" not in text or "OK" not in text or sentinel not in text:
        errors.append(f"raw-content:{name}")
    if count != 1 and f"Ran {count} tests" not in text:
        errors.append(f"test-count:{name}")
if (root / "overall.exit.txt").read_text(encoding="utf-8-sig").strip() != "0":
    errors.append("overall-exit")
refs = (root / "SOURCE_REFS.txt").read_text(encoding="utf-8-sig")
for value in ("0f50064a7ea7a69c51cb6751ac313b0c8b5ec9e2",
              "915c46d7f448003d82dd002d6e9fb34141e2712a",
              "3e498aebd77e500d5a7b1ac9d434d37350a9f597"):
    if value not in refs:
        errors.append(f"source-ref:{value}")
readme = (root / "README.md").read_text(encoding="utf-8-sig")
for phrase in ("No full MAP01 session", "No container or live allocation"):
    if phrase not in readme:
        errors.append(f"scope:{phrase}")
print(json.dumps({"checks": 5 + len(expected) + 3, "errors": errors,
                  "status": "PASS_SCOPED" if not errors else "FAIL"}, indent=2))
raise SystemExit(bool(errors))
