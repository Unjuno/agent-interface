# #4466 same-window GTK capture stability

This calibration follows the #3240 HOLD in PR #4464. Read [PREREG.md](PREREG.md), [CONSTRUCTION_PLAN.md](CONSTRUCTION_PLAN.md), `FREEZE.json`, and [RESULT.md](RESULT.md) in that order before interpreting evidence.

The formal run uses one no-input GTK/Xvfb session in a pinned Docker image. It samples the same target while unobscured, while a same-size decoy overlaps it, and after that decoy is moved beside it. This isolates XWD capture validity from application effect. Earlier failed/excluded construction runs remain under `evidence/construction*/`; formal evidence stays under `evidence/formal01/` and is never overwritten.

Build is not required when the frozen image ID is available locally. Formal reproduction:

```powershell
docker run --rm --pull=never --network none --read-only `
  --tmpfs /tmp:rw,size=64m --tmpfs /run:rw,size=16m `
  -v <repo>:/repo:ro -v <fresh-evidence-parent>:/evidence `
  -w /repo sha256:<frozen-image-id> `
  python research/integration/gtk_pixel_stability_4466_v1/construct_visibility.py `
    --allocation issue4466-visibility-formal01 --out /evidence/formal01

docker run --rm --pull=never --network none --read-only `
  --tmpfs /tmp:rw,size=16m -v <repo>:/repo:ro `
  -v <fresh-evidence-parent>:/evidence:ro -v <fresh-audit-parent>:/audit `
  -w /repo sha256:<frozen-image-id> `
  python research/integration/gtk_pixel_stability_4466_v1/audit_visibility.py `
    /evidence/formal01 --repo /repo --freeze research/integration/gtk_pixel_stability_4466_v1/FREEZE.json `
    --out /audit/audit.json
```

Run auditor construction controls separately with `audit_visibility.py --self-test`. The audit decision is scoped to this fixture and never implies #3240/#2606 completion.
