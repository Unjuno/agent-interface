# MAP01 terminal-wait boundary discrimination — T4

Status: prepared as an isolated host-only construction experiment. It does not run MAP01 and does not reuse a formal allocation.

## H / T / D / C / U

- **H:** The frozen `JsonSession.wait()` can produce the same `TimeoutError("session event timeout")` when (a) a terminal arrives with the wrong ID, (b) no terminal arrives while the child remains alive, or (c) the matching terminal arrives only after the wait deadline. In the late case, the reader may eventually retain the exact terminal after the caller has already timed out.
- **T:** Verify the exact current-main runner Git blob; launch four bounded synthetic Python children through that runner's unmodified `JsonSession`: matching terminal within the wait bound, wrong-ID terminal, no terminal, and matching terminal delayed beyond the wait bound. Retain child event timestamps, exact wait exception/outcome, all in-memory events, raw trace sidecars, process exit/termination and reader-thread cleanup. Run a separate auditor that reconstructs the literal-delimiter sidecars and checks every case against frozen criteria.
- **D:** `PASS_WAIT_BOUNDARY_DISCRIMINATION_SCOPED` iff the on-time exact ID is returned; wrong-ID, absent, and late-exact scenarios each yield the same timeout message while the child is alive; the wrong-ID case retains the wrong terminal, the absent case has none, and the late case eventually retains the matching terminal with child emission timestamp after the deadline; all children/readers clean up; hashes match. Unexpected exception/outcome is retained as FAIL/STOP with no retry.
- **C:** This establishes ambiguity in the session helper under controlled synthetic timing. It does not establish which path occurred in the consumed #3202/#3211 recovery arm, nor repair the runner or establish MAP01 behavior.
- **U:** No formal allocation, old workflow/runner execution, game, model/provider, GUI/input, GPU, Docker container, or retry. No resource lease is inferred from Docker Desktop's UI state or an idle container list.

## Freeze and collision checks

- Repository main at preparation: `bd77907946b7164e7513c3f5893f99348639e48a`.
- Exact source: `research/doom/map01_recovery_cover_matched_v2_runner_3211_diagnostic_v2.py`, current-main Git blob `f5caf71a743a563b7de046b82d44db7ebe49e829`.
- Search found no existing `map01-terminal-sync` branch beyond T1/T2/T3; no open PR was found for a wait-boundary test. This path/branch is distinct from writer-format experiments.
- Docker Desktop read-only UI showed Engine running, 0 running containers, 39 existing inactive entries, 5.15 GB RAM and 67.06% Engine CPU. The CLI `desktop-linux` server probe timed out. #5085 records another task's upcoming owner-bound CPU OrbStack reservation. Do not launch or alter containers.
- New namespace: `research/doom/map01_terminal_sync_wait_boundary_3211_t4_20261002/`.
- One candidate invocation; four synthetic child cases; one independent auditor; zero retries.

## Frozen implementation hashes

Captured in `FREEZE.json` immediately before the one-shot candidate. Do not alter the frozen inputs afterwards.
