# #3240 first-rung GTK application-effect control

This diagnostic targets the gap that kept #2850 open after a useful one-case
effect and an eight-case receipt-emission preflight: can a genuine application
state change be distinguished from a saved-looking fixture rendering that did
not result from the declared operation?

Read [PREREG.md](PREREG.md) before the result. The allocation has exactly two
fresh private Xvfb sessions in fixed order: a real GTK Ctrl+S action through the
public golden-v3 X11 adapter, then an untouched target application plus a
second same-title/same-geometry GTK decoy window. The decoy displays the exact
saved-looking text while the target receives no input. Raw XWD images, GTK
event/effect files, XID/PID/title/geometry, adapter receipts, empty releases,
cleanup and independent audit are retained.

The candidate audit is intentionally standard-library-only and runs in a
separate container invocation. It does not import the runner, runtime adapter,
or candidate GTK scorer. Source/image/package pins are in `FREEZE.json` once the
construction phase succeeds; raw evidence and its independent hash manifest
are written under the fresh allocation output directory.

Reproduce after building the pinned Dockerfile and verifying `FREEZE.json`:

```powershell
docker run --rm --pull=never --network none --read-only `
  --tmpfs /tmp:rw,size=128m --tmpfs /run:rw,size=16m `
  -v <repo>:/repo:ro -v <fresh-output-parent>:/evidence `
  -w /repo <frozen-image-id> `
  python research/integration/gtk_effect_control_3240_v1/run_probe.py --out /evidence/formal01

docker run --rm --pull=never --network none --read-only `
  --tmpfs /tmp:rw,size=64m -v <repo>:/repo:ro -v <fresh-output-parent>:/evidence:ro `
  -w /repo <frozen-image-id> `
  python research/integration/gtk_effect_control_3240_v1/audit_probe.py /evidence/formal01 `
    --out /evidence/audit.json
```

This first rung does not close #3240, satisfy the full formal #2606 matrix,
or establish a production/app-general task-success boundary. Do not call the
adapter's `partial`/`task_success=null` result a task PASS; the independent
application effect and its identity-bound evidence are reported separately.
