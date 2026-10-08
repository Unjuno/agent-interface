# A01 current-main source revalidation

Checked 2026-10-08 23:11:26 UTC on `origin/main`
`57337e95ecbecf7e762c8ec8091472b79e8ad49f`.

The retained allocation and candidate output are unchanged. The original
candidate remains one invocation with zero retries; this check did not invoke
the candidate, game, model, GUI, container, or OS input. All 20 frozen runtime
source files outside this evidence package match the SHA-256 values in
`FREEZE.json` at this `origin/main` commit. The retained raw result
`results/candidate_raw.json` was read by the independent auditor, which again
returned `PASS_METHOD_SCOPED` with 13/13 checks. The frozen package SHA-256
manifest also verifies without failures.

This revalidation confirms source identity and retained-result consistency on
the checked main tip. It does not upgrade the synthetic typed-signal result to
live GUI, physical-key, task-effect, or MAP01 evidence. A fresh authorized live
threat exposure and the remaining Issue #59 gates are still open.

Revalidation commands, run from the repository root:

```sh
python3 research/doom/v39_currentmain_health_guard_boundary_a01_20261009/audit.py \
  research/doom/v39_currentmain_health_guard_boundary_a01_20261009/results/candidate_raw.json
python3 - <<'PY'
import hashlib, json, subprocess
from pathlib import Path
root = Path("research/doom/v39_currentmain_health_guard_boundary_a01_20261009")
freeze = json.loads((root / "FREEZE.json").read_text())
prefix = "research/doom/v39_currentmain_health_guard_boundary_a01_20261009/"
checked = 0
for path, expected in freeze["files"].items():
    if path.startswith(prefix):
        continue
    current = subprocess.check_output(["git", "show", f"origin/main:{path}"])
    assert hashlib.sha256(current).hexdigest() == expected, path
    checked += 1
assert checked == 20, checked
print(f"PASS_CURRENT_MAIN_SOURCE_IDENTITY {checked}/20")
PY
```
