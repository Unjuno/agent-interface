# Issue #8057 T0 — internal versus environmental memory locus

## H / T / D / C / U

**H (scope):** On a frozen finite task-sequence fixture, the independent oracle should distinguish when a source-bound private note, task-owned environmental cue, both, neither, or safe rediscovery is available; invalidate stale information; preserve warning/restore safety as a hard gate; and account for all declared cost components. The authorship of the fixture cannot support an empirical memory-locus advantage.

**T:** Twelve two-step cases (repeated and heterogeneous task families), four arms (NEITHER, PRIVATE_NOTE, ENVIRONMENT_CUE, BOTH), 96 arm-step rows. Cases cover stable and changed app generations, obscured/edited cues, note omission/staleness, warning occlusion, cleanup failure, redundant/no-new-information cue, both channels unavailable, and safe rediscovery unavailable. Candidate output and independent oracle are separate processes; both read the frozen JSON fixture mounted read-only. No model, GUI, task effect, or UI actuation.

**D:** `PASS_METHOD_SCOPED`. Candidate and independent auditor exited 0; the auditor reconstructed all 96 rows exactly. Focused tests passed 13/13 normally and 13/13 under Python `-O`. Mutations for stale-note use, hidden-cue use, warning concealment, omitted cost, ignored restoration failure, and fabricated success with both channels unavailable were rejected. Correctness/resolution and safety remained separate fields.

**C:** All costs are authored abstract units, not model tokens, seconds, or user burden. Aggregate across this authored fixture: NEITHER 68 units, 22/24 resolved rows, 24/24 safety rows; PRIVATE_NOTE 109, 22/24, 24/24; ENVIRONMENT_CUE 87, 22/24, 20/24; BOTH 156, 22/24, 20/24. The cue arms fail the hard safety gate in the planted warning-occlusion and restoration-failure case. In the stable-visible repeated case, ENVIRONMENT_CUE costs 5 vs NEITHER 6; after app-generation change, NEITHER costs 8, PRIVATE_NOTE 8, and ENVIRONMENT_CUE 9. This is only an authored crossover illustration; it is not a held-out policy comparison or H pass.

**U:** No real GUI, model/provider, actual token count, timing distribution, user-owned/shared setting, warning risk, task correctness, or restoration behavior is established. No persistent UI change is authorized. T1 still requires a disposable GUI-like fixture and new ownership/freeze gates; an authored finite method pass does not imply that an environmental cue should be used.

## Provenance and retained command outcomes

- Base at branch creation: main `7c6f610fe73fe8135895e8715a81053ffb46b2a7` (2026-10-05); branch `research/8057-memory-locus-t0-20261005`; additive path `research/analysis/memory_locus_8057_t0_20261005/`.
- WSLc `3.0.1.0`; image `agent-interface/native-suite-wslc-a08:20261004`, image ID `sha256:1b4a8bd7c0fe372cc0cafa74af433b8ae1f73f1bee0f11a028f126b08b2c128a`; network disabled; source bind read-only; separate results bind writable; 1 CPU and 512 MiB requested.
- Every invocation reported: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` Requested hard memory/swap enforcement is therefore unverified.
- Candidate raw: `results/candidate.stdout.json` (96 rows); candidate exit 0. Independent audit raw: `results/audit.stdout.json`, `{"accepted": true, "reason": "accepted", "rows": 96}`; audit exit 0. Hashes and aggregate counts are bound in `results/RUN.json`; all retained artifacts are listed in `SHA256SUMS`.
- One post-run summary-only invocation failed before running a scientific process because PowerShell quoting truncated its Python `-c` string (`SyntaxError: '(' was never closed`). It did not invoke the candidate or auditor. The same read-only aggregation was immediately rerun with a safely passed argument and succeeded; original candidate/auditor outputs were not overwritten.

## Reproduction

From this directory, with the pinned image cached:

```powershell
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --volume "${PWD}:/work:ro" --workdir /work --entrypoint python agent-interface/native-suite-wslc-a08:20261004 -m unittest -v
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --volume "${PWD}:/work:ro" --workdir /work --entrypoint python agent-interface/native-suite-wslc-a08:20261004 -O -m unittest -v
```

The retained candidate/auditor execution is driven by `run_experiment.py`, with source mounted read-only and `results/` mounted separately as writable output. The image's repository-specific default entrypoint is bypassed with `--entrypoint python`.
