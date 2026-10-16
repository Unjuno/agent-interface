# R3 repeated mixed-app guarded recovery — durable-session allocation

This is a fresh execution allocation under Issue #3002. It preserves the consumed #1769 monolithic STOP and the synthetic-only #3002 durability preflight. Neither is pooled or rerun.

The only intended change to the R3 experiment is result collection: run the exact frozen `common.py` session once, atomically persist and `fsync` its complete returned row before starting the next session, then reconstruct the existing aggregate from those immutable batches. The original candidate/session code and gates are carried byte-for-byte in `upstream/SOURCE_BUNDLE.tar.gz.b64` and checked against its manifest before execution.

## H/T/D/C/U

- **H:** Persisting one completed session before starting the next makes the four-session, three-cycle R3 allocation recoverable and auditable without changing the guarded-recovery behavior or acceptance gates.
- **T:** Four fresh private Xvfb/Openbox sessions. Each runs the exact #1769 `common.run_session` once and its frozen `evaluate` gate. Each completed session is written as an immutable, atomic, fsynced batch before the next session starts. A separate network-disabled container audits only retained batch bytes and independently reconstructs the R3 acceptance gates. No model/provider, host desktop, user data, or external network.
- **D:** `PASS_MULTI_APP_GUARDED_RECOVERY_R3_SCOPED` only for four complete valid sessions and every original #1769 gate. Fewer complete sessions with every completed batch hash-valid is `HOLD_FORMAL_ALLOCATION_INCOMPLETE`. A completed row violating an R3 gate or cleanup/provenance evidence is `FAIL_RECOVERY_OR_INTEGRITY`. Failure to durably save a completed session is `STOP_NO_DURABLE_SESSION_BATCH`. No retries, replacements, pooling, or tuning.
- **C:** This local OrbStack container uses its observed Linux architecture and a newly built, frozen image. Chromium scheduling, X11 behavior, and cleanup may differ from the predecessor's host; no cross-architecture or cross-engine equivalence is implied.
- **U:** Four sessions and three cycles each are finite private-X11 evidence only. No endurance, arbitrary workflow, model utility, latency/token benefit, production, or human-tempo claim.

## Allocation roadmap

1. Verify original source bundle and construction provenance.
2. Build the isolated local image; run excluded construction and persistence/auditor tests.
3. Freeze exact source hashes, image ID/platform, outputs, gates, and fresh allocation identity; publish that freeze before formal execution.
4. Invoke the four-session runner exactly once in a detached OrbStack container; poll the same container to terminal state. Never restart it.
5. Audit retained batches in a separate fresh network-disabled container; preserve PASS, FAIL, HOLD, or STOP as observed.
6. Package source, per-session raw batches, logs, hashes, and audit under this additive directory; run local repository checks and open one reviewable PR.
7. Merge only after exact-head checks/review pass, then verify the evidence on main.

`upstream/FORMAL_STOP.json` and `upstream/FREEZE.json` are unchanged historical inputs. The new allocation receives its own freeze and result path.
