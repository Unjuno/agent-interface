# Issue #59 A03 — current-head scorer-tail command readiness construction

## Result

The candidate ran once against frozen PR #7692 source commit
3cc9fb83d15c8066386c4c4af3c10699f1829417 on Windows CPython 3.11. It exercised three OS socketpair cases with real select.select readiness:

| Case | Tail samples | Tail result | Command bytes remained unread | Later delivered |
|---|---:|---|---|---|
| Command ready before tail entry | 0 | CENSORED / command_ready | yes | once |
| Command sent during a synchronous 25 ms callback | 1 | CENSORED / command_ready | yes | once |
| Command sent during the normal wait after a 1 ms callback | 1 | CENSORED / command_ready | yes | once |

The candidate invocation passed these behavioral observations. The first independent audit (A01) incorrectly expected the normal iterator to return the newline delimiter; its failure is preserved in results/a03/AUDIT_V1.json and TEST_AUDIT_V1.*. The corrected A02 auditor recognizes that the adapter returns a decoded command line without the delimiter; it independently checks all three rows, all four source snapshots, and passes 28/28 checks. Four mutation tests pass in test_audit_v2.py.

The exact candidate was not rerun after the later test-only branch commit. The implementation source blob stayed unchanged; the combined current PR head passes the 69-test V39/scorer/lifecycle suite (one POSIX-only pipe test skipped), and the A02 independent audit plus six audit tests pass again. These are source regression checks, not another candidate allocation.

The candidate's post-tail iterator handling remains separately visible in the raw: an already-ready command can be delivered after one normal iterator sample. The tail itself performs no sample after detecting readiness and does not consume command bytes. The measured call durations (about 0.029 ms, 25.456 ms, and 2.295 ms for these individual constructions) are single observations, not latency estimates or performance claims.

## H / T / D / C / U

- **H:** On the frozen PR #7692 source, scorer-tail sampling will return command_ready before doing another tail sample when a command is already ready, becomes ready during a slow callback, or becomes ready during the normal inter-sample wait.
- **T:** One candidate invocation with three local socketpair cases, using real select.select and perf_counter_ns; retain command bytes through the tail and then check normal iterator delivery. No retries.
- **D:** Scoped PASS only if sample counts are 0/1/1, all tails are censored as command_ready, pending command bytes are unchanged, and each exact command is later delivered once. The candidate satisfied these checks and the corrected auditor passed 28/28.
- **C:** Synchronous callbacks and a socketpair do not model console stdin buffering, DoomGame getters, process teardown or the full V18 integration.
- **U:** One construction per case on Windows CPython 3.11. No real stdin, game, model, GUI, OS key input, safety, task effect, recovery, distribution, or MAP01 progress was measured.

The original A01 auditor discrepancy and the subsequent A02 correction are both retained; neither changed or reran the candidate result. Source snapshots are under source/, frozen runtime source commit and dependency hashes are in FREEZE.json, and candidate output is write-once at results/a03/RESULT.json. Runner and auditor code hashes were read back after the candidate invocation and are recorded in POST_RUN_READBACK.json; those hashes were not part of the pre-run freeze, which limits procedural reproducibility for this construction.

## Reproduction and retained commands

From this directory:

```powershell
python candidate.py
python audit_v2.py
python -m unittest -v test_audit_v2.py
```

The candidate refuses to overwrite its result. A new construction needs a new run ID and output directory.
