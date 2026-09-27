# Issue #2107 held-out GTK route

This additive experiment compares real `InputOwnerV10` synchronous F8 release
calls with `InputOwnerV11` interval receipts on a separate GTK3/Xvfb application
effect route. It keeps the earlier #869 Tk control, #2107 policy-stub evidence,
and focus/keymap rebase untouched.

Read `PREREGISTRATION.md` before the freeze or raw evidence. `FREEZE.json` pins
the source and local Docker image; `RESULT.md`, `evidence/formal01/`, and the
independent audit document one formal invocation. Construction output is not a
formal row. The independent standard-library auditor parses each retained XWD
and recomputes the decision trace without importing the candidate policy or
pixel classifier.

The fixture is a synthetic 400×180 GTK3 task: a real F8 key action changes a
red PENDING panel to a green DONE panel after a frozen delay relative to F8
press (before release), relative to F8 release (after release), or not at all.
The press- and release-relative delays are matched within each receipt-arm pair.
Application event/effect files are withheld
from the decision policy and used only by the independent scorer. The scorer
also checks key-up in the X-server keymap; this is not physical HID telemetry.

The release receipt is intentionally non-authoritative. The policy requires
both a fresh visible DONE panel and a fresh key-up sample to continue. A
valid receipt with a pending panel cannot continue; an ambiguous receipt is
normalized to UNKNOWN; a valid receipt with no application effect permits at
most one fresh-key-up retry before ABORT.

The outcome is scoped to one deterministic policy, one GTK fixture, and one
cached Linux/amd64 Docker image. Zero model/provider calls means no claim about
frontier-model decisions, tokens, user tasks, general GUI reliability, or
runtime readiness. `HOLD_NO_DECISION_VALUE` is an expected, meaningful result;
Issue #2107 remains open unless its broader acceptance is met.

After `FREEZE.json` and its source commit exist, reproduction is two separate
Docker Desktop invocations. Replace the two Windows paths and the 40-character
commit with the exact frozen checkout values. The output directory must be new.

```powershell
docker run --rm --pull=never --network none --read-only `
  --tmpfs /tmp:rw,size=128m `
  -v C:/path/to/frozen/repo:/repo:ro `
  -v C:/path/to/frozen/repo/research/integration/release_telemetry_gtk_route_2107_v1/evidence:/evidence `
  -w /repo --entrypoint /usr/bin/python3 `
  sha256:eb3ce9f5bd0cf358664b9d1ff9bce4cf2ce9f82f72ec700222046fb8fe8b96ba `
  /repo/research/integration/release_telemetry_gtk_route_2107_v1/runner.py `
  --mode formal --out /evidence/formal01 --freeze-commit <frozen-commit>

docker run --rm --pull=never --network none --read-only `
  --tmpfs /tmp:rw,size=32m `
  -v C:/path/to/frozen/repo:/repo:ro `
  -v C:/path/to/frozen/repo/research/integration/release_telemetry_gtk_route_2107_v1/evidence:/evidence:ro `
  -v C:/path/to/new/audit-output:/auditout `
  -w /repo --entrypoint /usr/bin/python3 `
  sha256:eb3ce9f5bd0cf358664b9d1ff9bce4cf2ce9f82f72ec700222046fb8fe8b96ba `
  /repo/research/integration/release_telemetry_gtk_route_2107_v1/audit.py `
  /evidence/formal01 --source-root /repo --out /auditout/AUDIT.json
```

**Current status: construction passes; preregistered formal run not yet executed.** Construction 10 used the pinned image without changing it and replaced the fixture's Cairo-dependent custom draw callback with GTK's standard GdkPixbuf image replacement. All four smoke cases completed, and the independent raw-evidence audit returned `CONSTRUCTION_AUDIT_PASS` with `errors: []`. The earlier constructions 04–08 remain unchanged STOP evidence; construction 09 retains a fixture syntax STOP. This establishes the held-out route's visible effect gate only—not decision utility, formal outcome, model/task quality, or Issue #2107 acceptance. The H/T/D/C/U and thresholds are public in this PR. After a fresh source freeze/commit, run the 56-session formal block exactly once and then perform the separate independent raw-evidence audit.