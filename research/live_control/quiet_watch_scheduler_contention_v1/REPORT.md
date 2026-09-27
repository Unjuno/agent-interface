# Same-core contention and 2 ms scheduler tails

Task `QUIET-WATCH-SCHEDULER-CONTENTION-20260916-001`, Issue #316.

Disposition: **`CONTENTION_TAIL_REPRODUCED_SCOPED`**.

This is a scheduler-attribution experiment only. It does not change or rerun #270/#283 watcher allocations and does not modify shared runtime.

## Question
A minimal Python loop sleeps to an absolute monotonic schedule every 2 ms for 600 ms (300 samples). The only intervention is one independent busy-loop process pinned to the same logical CPU. Twenty matched pairs alternate arm order.

## Formal first outcome
- median paired contended/idle max-wake-lateness ratio: **3.8408155109582367** (gate >=2.0)
- contended median block max lateness: **3.596879 ms** (gate >=1.0 ms)
- contended blocks with max lateness >=1 ms: **20/20** (gate >=10/20)
- idle median block max lateness: **1.2517045 ms**
- idle median p99 lateness: **0.36427714 ms**
- contended median p99 lateness: **1.561177595 ms**
- formal decision: **`CONTENTION_TAIL_REPRODUCED_SCOPED`**

The same-core contention arm therefore reproduces several-millisecond wake tails without X11, Tk, ROI acquisition or predicate work. That makes CPU contention a sufficient mechanism in this fixture, not proof that it caused every tail in #270/#283.

## Important counterevidence / limits
Idle is not tail-free: one idle block reached **61.64384 ms** max lateness and four idle blocks had at least one >=2 ms late wake. This shows host/virtualization/noisy-neighbor effects exist independently. Conversely, every contended block had >=1 ms max lateness, while its largest max was 11.975464 ms.

The synthetic busy loop is stronger and more stationary than real X11/Tk load. CPU frequency, Linux scheduling and virtualization are uncontrolled. No hard-real-time, release-latency, arbitrary-GUI or production claim follows.

## Audit
Frozen `audit.py` passes the formal result and rejects decision/max/count mutations, but a post-formal negative control showed it failed to verify `late == wake - due`. The frozen audit is retained unchanged. Additive `audit_strict_posthoc.py` verifies tuple arithmetic, exact 2 ms due increments, block summaries and the frozen decision; it passes the formal result and rejects decision, max-lateness, sample-delta and due-step mutations. No formal timing block was rerun.

## Retention
Formal raw JSON SHA-256 is `dd3b0373ba82ac632154df51a547d9d1d1304f60695d6461427a394746e144fc` (1,266,373 bytes). Due to the current connector text-upload boundary, this publication retains all decision-relevant per-block statistics in `decision_evidence.json` plus the raw digest, but not the full 12,000 timestamp tuples on GitHub. The full raw remains local to this execution session. This is a reproducibility limitation and prevents exact posthoc reclassification from GitHub alone.

## Next rung
Before changing scheduling policy, add one **other-core contention control** with the same timing loop. If same-core contention is the causal mechanism, moving the busy process to a different logical CPU should materially reduce the tail inflation. This is a new allocation and must not reuse #316 identity.
