# X11 resync-cut integration intake

**RETAINED_EVIDENCE_PASS / SHARED_RUNTIME_ADOPTION_HOLD.**

Newly published #4318 / PR #5212 evidence was restored from exact main bytes and re-audited in a cached, hash-pinned Docker Python image. The container had no network, read-only root/input mount, 1 CPU, 256 MiB memory, 64 PIDs and no added capabilities. It exited 0 without OOM. No X11 actor, model, GUI experiment or frozen allocation was started.

The unchanged raw auditor reproduced the saved AUDIT.json byte-for-byte: 2,478 checks, errors=[], PASS_X11_RESYNC_CUT_SCOPED. All 12 copied-evidence corruption controls also exactly reproduced the saved results and rejected effective mutations. Seven frozen policy tests passed. This is container execution of the existing same-author auditor, not independent human review or a new scientific allocation.

## Applicability to current production paths

| Research prerequisite | Current interface | Integration decision |
|---|---|---|
| Producer-authored contiguous state sequence and source epoch | Public captures have UUID/timestamp metadata; guarded sequence increments per capture | Capture count cannot stand in for application-state sequence |
| Complete state snapshot at a known cut | PNG plus target metadata, with metadata recheck | Neither complete application state nor arbitrary-GUI atomicity is established |
| Explicit gap/frontier and preserved missing-history identities | Input recovery verifies key/button neutrality and advances binding revision | Motor recovery is a different contract; do not claim event-history recovery |
| Delayed envelopes applied to a current-state reducer | Primary relay allows one outstanding call; image reuse references acknowledged PNG bytes | No matching event-reducer insertion point in this path |

The candidate is useful only after the producer/snapshot/gap contracts exist. Importing its reducer now would add unsupported completeness semantics. Do not reinterpret X event serials, locally minted observation counts, unchanged images, successful focus, or a released key as those contracts. Do not merge automatic resync, event acquisition or sensor development as part of this intake.

The original result demonstrates scoped ordering behavior for a cooperative single-property producer. It does not establish arbitrary desktop recovery, lost-history restoration, input authority, natural failure rates, task benefit, lower latency, fewer model calls or tokens. The existing primary UI task remains the current source of evidence about useful feedback and save transitions.

## Retained verification

Run `python3 -O runtime/results/resync-cut-intake-01/verify.py`. It checks every retained byte, exact saved/new auditor and control outputs, terminal container state and isolation, source pins, and the explicit adoption HOLD. raw.tar.gz includes the exact published package, all 669 restored evidence files, 15 source files, current interface sources, Docker commands/inspection/stdout and the integration mapping.

The Docker container is stopped and retained for inspection; its original evidence mounts were read-only. Frozen files and prior experiment outcomes are unchanged. Future work should integrate only a compatible producer contract with separately demonstrated task benefit, rather than transplanting this reducer into screen capture.
