# Per-key synthetic hold-time envelope probe

**Classification:** Post-freeze one-shot 30-cycle software-construction measurement, pinned to main `27f6e9ff02f21afbe56579b72063c19b2dbd74bb` and #7440 head `99b7d130742b4e884709a862bc074d15e6b42ac9`. No source files in the repository were changed by this probe.

**Hypothesis (H):** The current InputTransitionOwnerV4/InputOwnerV12 admission and explicit-up receipts can bound the synthetic key-held interval for a single key using their timestamps, without sampling input state between the key-down and key-up calls.

**Test (T):** Freeze exact source hashes, decision rule, and one 30-cycle block. Each cycle creates a fresh fake owner and lease, requests `W` down, requests explicit `W` up, then samples owner state. The fake Xlib records key press/release events. A separate raw-only auditor recomputes intervals from the four timestamps.

**Decision (D):** PASS only if all 30 cycles have matching admission/up key and lease receipts, a consistent owner id, valid non-cancelled up, monotonic timestamps, verified-empty post-up state, the fake press/release pair, and the recomputed lower bound is no greater than the upper bound. Source hashes must match the pre-run freeze. No retries.

The conservative per-cycle envelope is:

- lower endpoint: `max(0, release_call_started_ns - input_ack_ns)`
- upper endpoint: `release_call_returned_ns - admitted_ns`

The down request occurs after `admitted_ns` and is synchronized before `input_ack_ns`; the up request is sent after `release_call_started_ns` and synchronized before `release_call_returned_ns`. These bound the XTest/server-side synthetic key interval. They do not bound when an application processes the key event.

**Results:** 30/30 cycles completed without errors. The raw-only auditor passed 300/300 row checks and 11/11 aggregate checks, including frozen source hashes. Lower endpoints ranged 13.8–43.1 μs (median 19.1 μs); upper endpoints ranged 41.2–91.6 μs (median 54.5 μs); interval width ranged 27.4–65.0 μs (median 36.2 μs). Per-endpoint medians are marginal summaries, not a single representative interval. `py_compile` passed.

**Counterevidence (C):** Every cycle is a controlled fake-Xlib sequence on one Windows Python host. Timing includes Python scheduling, queue handoff, XTest request processing, and synchronization. This does not validate a physical device, real X server scheduling, app event processing, or the DOOM session backend's end-to-end emission/storage.

**Uncertainty (U):** No game, model, GUI, useful task feedback, bounded recovery, matched human comparison, formal allocation, or live-control efficacy was tested. A preceding one-cycle pilot on earlier source identities was explicitly excluded from this decision. The full r134 research goal remains open.

Reproduction: `python -B run_hold_bound_30.py`, followed by `python -B audit_hold_bound_30.py`. The frozen source identities are in `PRE-RUN.json`, raw rows in `RAW-30.json`, run receipt in `RUN.json`, and hashes in `SHA256SUMS.txt`.

**Repository binding:** The `research/live_control/` files nested under this result directory are byte-for-byte copies of the frozen sources, retained so `audit_hold_bound_30.py` can verify the original manifest without rewriting it. `audit_repo_sources.py` independently checks those copies against both the tracked files in this PR checkout and the same frozen SHA-256 values; its output is `REPO-SOURCE-AUDIT.json`. The run remains pinned to main `27f6e9ff02f21afbe56579b72063c19b2dbd74bb`; later main movement does not retarget the frozen sample.

**Main movement check:** At review preparation, `main` had advanced to `c3808eb887f8a85a80a2e9cfb19960547164abd8`. GitHub's compare from the frozen base (`27f6e9ff02f21afbe56579b72063c19b2dbd74bb`) reports no changed files under `research/live_control/`; the sample remains identified by its original freeze and was not rerun or relabeled as a new-main measurement.
