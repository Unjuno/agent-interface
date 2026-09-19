# Registered comparison, pair 1: no recovery-call reduction

Pair 1 of `recovery_comparison_plan_v1.json` was executed in its registered A then
B order: Inkscape, seed 201, one additional clock boundary. The same initial PNG,
task steps, runtime source manifest and report/image presentation were used. Each
arm had five explicit stage calls: initial, deliberate observe/stale setup,
recovery/history/image, move/save/image, finish. The assistant reviewed the recovery
image before the move stage. Setup captures varied (3 versus 2), and that evidence
is retained rather than treated as identical full application state.

| Outcome | A: explicit read | B: helper |
|---|---:|---:|
| Recovery model orchestration calls | 1 | 1 |
| Recovery socket reads | 1 | 1 |
| Total socket exchanges including recovery | 8 | 10 |
| Initial move terminal | completed | needs_decision |
| Final saved task contract | passes | passes after explicit recovery |
| Capture to independent evaluation | 51.799 s | 104.123 s |

There is no call-count improvement in this depth-1 pair. The full elapsed B-minus-A
difference is +52.323 seconds, retaining diagnosis and recovery. It is not a causal
latency estimate: exact model identity/configuration and model receipt timestamps
were unavailable, as explicitly recorded before each arm's first query. The plan's
model-performance qualification condition therefore is not met. Do not replace
these missing measurements with a generic model-family label.

## Focus interruption retained

B's initial click was admitted, but its input owner recorded `focus_changed` release
before the subsequent Right hold. That move program ended `needs_decision` after
one completed step with verified release and no key admissions. The sampled image
contexts before and after capture match; they do not exclude a transient focus
change between samples. The owner log provides more specific evidence than the
terminal's null error field. No helper-induced focus cause is established.

The assistant inspected the returned image and relevant source, then explicitly
submitted a new recovery program, increasing only the click duration to 80 ms.
This is an unplanned recovery action, not a silent change to the registered task
steps or a replacement arm. The original interrupted program remains recorded.
The final saved SVG is x=52, y=50, width=40, height=30, transform absent, agreeing
with A's legacy move-right result. This contract does not require the seed's dx as
a precise displacement. The final B finish read starts at its original move cursor
and includes the intervening recovery history; the audit verifies that overlap.

## Audit and remaining work

`results/recovery-pair1-01` preserves all stages, raw logs, sources, frames, owner
events, final SVG, and B's additional recovery. `audit_recovery_pair1_v1.py` verifies
18 exact AIT/PNG frames, all 92 unique runtime records across the two arms, each
received slice against the raw log including overlap, identical initial PNG and
registered move steps, source hashes, the actual assembled history used for move,
the interrupted terminal and release, and final saved task results. Both bridge
handles were polled to exit zero. Per-child structured cleanup remains unavailable
in this old desktop entry point.

The common per-stage runner was written before either arm and its hash captured
before each arm's initial query. It covers pair 1 only; do not silently modify its
measured source to implement later pairs. Sources pinned by the registered plan
were unchanged. Presentation experience/counts are conversation reports, not
instrumented model receipts. Output budgets were held equal per corresponding
stage and original-image detail used; available context and inference duration are
not thereby proven identical.

**Progress: 2 of 8 scheduled episodes executed; 6 remain.** Next is pair 2,
Inkscape depth 3, B then A. Keep this failed-first-attempt outcome in the study;
do not rerun pair 1 to obtain a cleaner result. The helper remains unpromoted as
a speed optimization. Any new protocol interpretation or changed gate requires
an explicitly versioned amendment, preserving the original plan and pair.

```sh
python3 research/live_control/audit_recovery_pair1_v1.py
```
