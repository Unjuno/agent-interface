# MAP01 finish scorer closure v2

Status: **OFFLINE PASS — live ViZDoom/MAP01 integration remains UNPROVEN.**

Task: `O3-G2-MAP01-FINISH-SCORER-CLOSURE-002`

Base: `7356970b15406c74bd2b404327f39c2e6b546022`

## Problem found

Telemetry-session v1 stops `MainThreadScorerPolling` immediately when the command handler returns `False`. In the historical v12 finish path, `finish` may close the executor and perform a final ViZDoom refresh before computing `post_control_score`. Therefore the last periodic independent scorer sample can precede the state used by `post_control_score`. Synthetic session v1 proved periodic scheduling, but it did not prove terminal-state agreement.

## Candidate

`map01_telemetry_session_v2.py` adds one narrow closure:

- command routing records whether a terminal loop stop was `finish` or `save_fixture`;
- only a successful `finish` causes exactly one additional scorer sample after the finish callback returns;
- that sample stays on the same polling/scorer owner thread;
- it is persisted in scorer-owned `independent-scorer-final.json` with `controller_visible=false`;
- an optional score provider is compared strictly against `map_exit`, `episode_finished`, `player_dead`, `death_count`, and `kill_count`;
- disagreement is fail-closed;
- `save_fixture` does not fabricate a final scorer record;
- no scorer payload is emitted through the controller emitter.

This module does not yet alter `session_map01_v12.py`, does not grant input authority, and does not claim live ViZDoom behavior.

## Container validation

Environment: CPython 3.13.5, Linux 6.18.44 x86_64; CPU clock not pinned; ViZDoom unavailable.

Construction checks:

- `py_compile`: PASS;
- deterministic regressions: **6/6 PASS**;
- controller-stream scorer leakage check: PASS;
- strict bool/int mismatch rejection: PASS;
- score disagreement fail-closed: PASS.

A 500-trial synthetic finish benchmark mutated fake game state only inside the finish callback. Every trial produced one periodic record plus one post-finish record and exact terminal-score agreement.

| Metric | Median | p95 | p99 | Max |
|---|---:|---:|---:|---:|
| one-command loop + final persistence | 161.369 us | 265.021 us | 392.069 us | 661.657 us |
| final fake scorer callback | 1.061 us | 1.242 us | 1.623 us | 171.633 us |

These values are container/fake-object measurements only; they are not ViZDoom getter or gameplay latency.

## H / T / D / C / U

### H — falsifiable hypothesis

A successful v12-compatible `finish` can be followed by exactly one same-thread independent final scorer sample, persisted outside controller channels, and that sample can fail closed unless it exactly agrees with the historical terminal score fields.

### T — minimum validation

Six deterministic regressions plus 500 synthetic one-command trials. The decisive negative control intentionally changes `post_control_score.map_exit`; validation must raise rather than accept the mismatch.

### D — decision

**PASS for offline finish-boundary closure. LIVE MAP01/ViZDoom = UNPROVEN.**

The previous synthetic-session result is strengthened: terminal agreement now has an explicit mechanism rather than an unstated assumption. This still does not authorize recovery-vs-coast efficacy work.

### C — ways the result can break

- real ViZDoom getters may block or differ after final `advance_action`;
- wiring into `session_map01_v12` may accidentally duplicate or reorder the historical finish refresh;
- release-telemetry v3 composition may perturb input cleanup or scorer cadence;
- filesystem pressure may alter persistence latency;
- a real terminal engine state may expose fields not represented by the five-field equality contract.

### U — uncertainty

Dominant uncertainty remains absence of ViZDoom in this container. No live timing distribution or causal performance claim is justified.

## Next gate

Create a separately versioned real session (do not mutate retained v12) that composes:

1. current release telemetry v3 backend;
2. periodic independent scorer v1;
3. this post-finish closure v2;
4. historical v12 command/release behavior.

Freeze exact hashes and run one no-retry real MAP01 telemetry-only allocation in a ViZDoom/X11 environment. Require owner-thread consistency, zero scorer leakage into `events.jsonl`/`delivered.jsonl`, retained missed-period/getter timings, unchanged release semantics, and exact final-score agreement. Retain any failure without retry.
