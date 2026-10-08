# V39 cover-admission invalidation: current-main replay A01

## Question and scope

This replay checks one construction-level ordering question on current `main`: when a hard-health observation is ahead of a matching `accepted` event in the session FIFO, does V39's initial `submit_cover` wait notice the invalidation before returning acceptance? The comparison runs the exact main wait function once without an observation monitor and once through the existing #7589 Draft helper. It is an inert source-composition test, not a full controller run.

The run used main `6f34c5c0c5bc3116d8e7c25f29aa1b92cc4a01b1`. Before publication, main advanced to `e7c916989da30741b00c234efd264067d0899851`; readback confirmed that both measured V39 controller and wait-test Git blobs are unchanged at that newer main.

### H / T / D / C / U

- **H:** Current-main V39 cover admission can consume a hard-health observation as an unrelated event and return the later `accepted` event without invoking its validity monitor. The #7589 helper should surface that same observation as a policy invalidation first.
- **T:** Pin main `6f34c5c0c5bc3116d8e7c25f29aa1b92cc4a01b1` and #7589 head `763ff69a531eb47a6a3f033f56171dffc80afa23`. Execute the exact nested V39 `wait` function against one FIFO sequence: observation sequence 17 / health 70, then accepted `cover-0`. Compare the source-extracted #7589 `wait_for_cover_acceptance` helper against the same wait function. Keep the FIFO, monitor, predicate, and event order fixed.
- **D:** `PASS_MAIN_ADMISSION_GAP_REPRODUCED` only if source audit confirms main's `submit_cover` calls wait without `observation_monitor`, the current-main wait returns `accepted` without calling the monitor, and the #7589 helper returns `policy_invalidation` while leaving `accepted` queued. Otherwise retain the observed mismatch or STOP; do not infer runtime input or effects.
- **C:** This tests one FIFO ordering and the wait/helper composition. The controller may receive later observations and other guards may act; the test does not establish behavior under different schedules.
- **U:** No full `submit_cover` invocation, session, X server, OS input, game, model, GUI, task effect, release, latency, recovery, or threat outcome is tested. No allocation or authority is requested or inferred.

## Result

The scoped gate passed. Main's extracted wait consumed the observation and returned the later `accepted` event; its monitor saw no sequence and the FIFO was empty. Using the #7589 helper with the same wait and FIFO returned `policy_invalidation` for `health_below_floor`, recorded sequence 17, and left `accepted` queued. The independent raw-only auditor passed 22/22 checks.

The current-main wait tests pass 7/7. The #7589 Draft wait tests pass 8/8 when pointed at the Draft controller source. An initial attempt to run those Draft tests against main stopped in the test harness because the current-main source does not define `wait_for_cover_acceptance`; that source-selection STOP is preserved in `TEST_SOURCE_MISMATCH.json` and is not a scientific failure.

The WSLc 3.0.1.0 kernel reported that swap-limit capability/cgroup support is unavailable. The requested 512 MiB memory limit is therefore not treated as verified enforcement.

## Reproduction

Use cached image `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364` (Python 3.12 slim), `--pull never --network none --cpus 1 --memory 512m`. Mount this package directory read-only as `/input` and a new, empty writable directory as `/output`.

```text
python /input/candidate.py
python /input/audit.py
V39_WAIT_SOURCE=/input/main.py python -B /input/main_test.py -v
V39_WAIT_SOURCE=/input/pr.py python -B /input/pr_test.py -v
```

The executed code is preserved unchanged as `candidate_executed.py` and `audit_executed.py`; their hashes are in `FREEZE.json`. The replay-safe `candidate.py` and `audit.py` add preflight refusal if their output already exists. Run them only with a fresh output directory. The executed candidate ran once; its raw output was audited in one separate container. The auditor does not import the candidate. Exact main and PR source snapshots, tests, raw JSON, audit JSON, source-selection STOP, command notes, and checksums are retained here.

## Integration implication

This is current-main compatibility evidence for the admission gap already addressed by open Draft PR #7589. That PR was based on `63980603e4bb6e4b128ed07af3bf7023bc2d4734`, older than this replay's main. The result supports revalidating/rebasing that existing fix; it does not authorize changes to its branch, substitute for independent review, or justify merging. No live #59 gate is closed.
