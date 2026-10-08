# `authority_ended` caller restart durability discovery v1

Status: **RETAIN_DURABLE_TOKEN_STATE_CANDIDATE** offline and **PASS_LIVE_DURABLE_RESTART** in one model-free real ViZDoom/X11 session. The remaining gap is the crash window after durable consume but before OS submit.

## Discovery sequence

This series follows the one-variable discovery rule and starts from the live duplicate-receipt result. Each step adds only the minimum state needed by the failure immediately before it.

### A. Empty restart reproduces receipt remint

The in-memory receipt ledger correctly blocks duplicate terminals while the caller stays alive, but a fresh empty ledger loses `issued_ids`. Replaying the exact retained live receipt after issue+consume mints a new token and revalidates on a later sequence. **Baseline restart failure reproduced.**

A first repair exported only the issued runtime authority-end IDs and rehydrated them into a fresh ledger. It rejected the old receipt before/after consume and allowed one distinct runtime ID. This proved state transfer was sufficient for replay safety, but made no filesystem/crash-durability claim.

### B. Atomic durable issued-ID set

A JSON issued-ID state file was written through exclusive temp file -> file fsync -> atomic replace -> parent-directory fsync. Separate Python subprocesses verified:

- restart rejects an already committed ID;
- crash after temp fsync but before replace leaves the old canonical state intact;
- crash after replace+directory fsync leaves the new ID durably rejected;
- corrupt/missing restart state fails closed rather than silently becoming empty.

20 persisted issues on this container filesystem: median **0.240 ms**, range **0.219–0.994 ms**. This was safe but lost liveness for an issued-but-unconsumed token because only the ID set survived.

### C. Durable pending/consumed token state

The final offline candidate stores:

```text
authority_end_id -> { post_sequence, status = pending | consumed }
```

`issue()` validates the normal `authority_ended` receipt, persists `pending` before handing out a token, and `consume()` durably transitions `pending -> consumed`. `recover_pending()` reconstructs the same logical token after caller restart. Multiple recovered token objects are harmless because the durable consume transition is the single execution gate.

Frozen subprocess matrix: **13/13 PASS**.

- restart recovers pending token with the same ID/sequence;
- duplicate terminal issue while pending rejects;
- two recovered token objects cannot both consume;
- restart after consume cannot recover or reissue the ID;
- crash after pending replace/fsync but before issue return recovers the pending token;
- crash after consumed replace/fsync but before consume return remains consumed after restart (safe but may lose liveness);
- distinct runtime ID issues/consumes normally;
- corrupt state fails closed.

20 independent one-ID persistence trials:

| operation | median | range |
|---|---:|---:|
| durable issue | **0.175 ms** | 0.169–0.616 ms |
| durable consume | **0.230 ms** | 0.221–0.407 ms |

Conditions: CPython 3.13.5, Linux container filesystem, shared Xeon Platinum 8573C, frequency unpinned. These are local storage measurements, not general latency guarantees.

## Live process-boundary integration

Runtime: immutable source base `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`, ViZDoom 1.3.0 / Freedoom MAP01 / `map01-threat-contact-v2`, skill 1, ASYNC_SPECTATOR 35 Hz, private Xvfb/Openbox, zero model calls.

Construction seed 994399 first exposed a wrapper-only startup error: the harness pre-created the output directory while the session contract requires it not to exist. No candidate logic/formal allocation ran. Removing that one premature mkdir produced a passing smoke. Formal seed **994400**, one session, zero retry.

The ViZDoom session remained alive while **each durable-ledger operation ran in a fresh Python subprocess**:

1. first scheduled authority expires -> `authority_ended`, verified empty release, post sequence 2;
2. subprocess A durably issues `pending` for runtime ID `2ff0b25889cd4bac9ae5a18dbf568123`;
3. subprocess B reconstructs the same pending token;
4. a duplicate-issue subprocess rejects it; input since first release remains zero;
5. observe-only advances to sequence 3;
6. a fresh revalidation subprocess returns `revalidated`;
7. a fresh consume subprocess persists `consumed`;
8. only then one 80 ms physical `Shift_L` action is submitted;
9. second terminal completes with verified empty release;
10. fresh post-consume subprocesses reject both recovery and duplicate issue; a fresh load sees exactly the first ID as `consumed`.

Formal result: **PASS_LIVE_DURABLE_RESTART**.

Hard outcomes:

- input before second submit: **0**;
- intended second physical input admissions: **1**;
- total post-first-release input admissions: **1**;
- input after second release before finish: **0**;
- strict five-field final independent scorer agreement: PASS.

Timing observations in this one session:

- first deadline -> verified empty: **0.672 ms**;
- first verified empty -> second physical input: **281.875 ms**;
- second input -> second verified empty: **132.050 ms**.

The 281.875 ms includes multiple deliberately separate Python processes, observe-only execution, durable fsyncs and revalidation. It is not a performance target.

## H / T / D / C / U

**H.** Persisting the runtime-owned authority-end identity plus `post_sequence` and `pending/consumed` status is sufficient to preserve duplicate-replay safety and recover an unconsumed replan token across caller process boundaries without reopening old input authority.

**T.** Sequential offline restart/crash matrices, then one fresh real ViZDoom/X11 formal session whose ledger operations each run in a separate Python subprocess while the GUI session remains live.

**D.** **RETAIN_DURABLE_TOKEN_STATE_CANDIDATE / PASS_LIVE_DURABLE_RESTART.** All frozen offline and live gates pass.

**C.** A hard crash after `consumed` is durably persisted but before the new OS-input submission can lose liveness: restart correctly refuses replay even if no second action was sent. Moving consume after submit would create the opposite duplicate-risk window. Exactly-once external side effects cannot be claimed from this ledger alone.

**U.** Single-writer local state file, one live fixture/seed/key/host, no model, no cross-domain transfer. Filesystem guarantees depend on host/kernel/storage. No authentication against malicious state-file tampering.

## Next smallest experiment

Do not invent another transaction protocol immediately. The repository already contains a `durable_submit` direction for uncertain delivery. Compare this consumed-before-submit crash gap against that existing contract and test whether the composition can return an explicit `PENDING/UNKNOWN` delivery state without blind replay. If the existing mechanism already closes the gap, compose rather than duplicate it. Only after that should a bounded model-in-loop handoff be considered.
