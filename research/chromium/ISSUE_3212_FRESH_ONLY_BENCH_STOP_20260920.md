# Issue #3212 — matched fresh-only benchmark stopped at Chromium readiness (2026-09-20)

This is a preserved failure/stop record, not a performance result. Earlier successful matched evidence and all prior raw artifacts remain unchanged.

## H/T/D/C/U

- **H:** A same-case `FRESH_ONLY` arm can be compared with `REUSABLE_PLUS_FRESH_GATE` while charging launch, readiness, model-wait, and reacquisition costs.
- **T:** Docker image `mixed-formal-2992-debian:20260920` (`sha256:766abfd10382ab8b59ed793094a685481190f840d338b7bc4664ca162a2da619`), `--network none`, Xvfb, real Chromium, three fresh launches followed by a reuse arm, separate CDP ports.
- **D:** The fresh arm failed its ready/CDP gate in all three attempts at `15005.714`, `15010.065`, and `15029.188` ms. No valid DOM effect was observed. The reuse arm consequently had `fresh_gate=false` and no effect in all three rows. Raw SHA-256: `1296b8df75ade08d0cd6b26e5911f3d2e4d1482c073bbb86ae720e8c708d89b9`.
- **C:** `STOP_CHROMIUM_RUNNER`. This run provides no evidence for or against reuse benefit and must not be merged as PASS.
- **U:** The successful orchestrator runner in the same image/environment still works, so the failure is scoped to this benchmark runner's launch/CDP path. Diagnose that path before rerunning; retain `HOLD_REUSE_BENEFIT_UNMEASURED`.

## Preserved raw outcome

```json
{"fresh_launch_ready_ms":[15005.714,15010.065,15029.188],"fresh_effect":"0/3","reuse_gate":"0/3","reuse_effect":"0/3","decision":"STOP_CHROMIUM_RUNNER"}
```

The full raw JSON and runner are stored under `research/chromium/issue-3212-fresh-only-benchmark-stop-v1/`.
