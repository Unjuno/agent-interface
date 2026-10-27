# V39 measurement-session dispatch construction A01

## H / T / D / C / U

**H.** Current-main V39 has an explicit `--measurement-session` switch. With the switch, the exact `session_command` selects `session_map01_v15.py`, and the run report should label the mode `v15_scorer_only_per_key_release`. Without it, the command should preserve the V12 default and report `v12_default`. The selected V15 source chain should contain the per-key release instrumentation. This checks a future-run dispatch contract; it cannot repair or reinterpret a historical run.

**T.** Freeze current main and seven source blobs. AST-execute the exact V39 `session_command` with the exact parser option extracted from `main`, evaluate the exact report's measurement label expression, and trace the V15 session's release backend to the transition owner and V12 key owner. Run normal and optimized modes, plus independent output reconstruction and mutation controls. Do not start the session, game, model, GUI, container, or input path.

**D.** PASS only if both CLI states parse as frozen, default and measurement commands choose V12 and V15 respectively, all other session arguments are preserved, labels match the chosen path, and the V15 release source chain contains the pinned per-key timing fields. Any mismatched mode/path/label or source identity is FAIL.

**C.** The past V39 run's source manifest showed V12 without the V15 overlay. This construction result does not prove what arguments its absent launcher passed, and the report label is generated only after the live run proceeds.

**U.** This verifies the current command-construction seam and source capability only. It does not establish runtime launch selection, physical key state, useful feedback onset, recovery, task effect, threat response, or MAP01 outcome. A fresh V39 threat exposure remains separately gated.

## Result

The exact current-main helper selects `session_map01_v12.py` for the default parser state and `session_map01_v15.py` when `--measurement-session` is present. The report label follows the same flag in both cases. The selected V15 composition imports the owner-thread release backend, which composes release backend V2 and transition owner V4; transition owner V4 delegates to InputOwner V12, whose release receipts include per-key attempt and interval fields. Normal and optimized outputs match, and the independent auditor rejects path and label mutations.

## Safe reproduction

`run_modes.py` refuses output paths inside this evidence package and refuses an existing output directory. By default it creates a unique directory in the system temporary area, leaves every retained artifact untouched, and prints the results directory. It checks that the target volume has at least 64 KiB free before running, then runs the candidate twice, audits the output, and writes hashes for the external result bundle. If system temp is full, pass `--output-dir` on another volume.

```powershell
$resultsRoot = 'D:\CodexResearchTmp' # choose any writable volume with at least 64 KiB free
$resultsDir = Join-Path $resultsRoot ("v39-dispatch-" + [guid]::NewGuid().ToString("N"))
$run = python -B research/doom/v39_measurement_dispatch_a01_20261008/run_modes.py --output-dir $resultsDir | ConvertFrom-Json
python -B research/doom/v39_measurement_dispatch_a01_20261008/verify.py --results-dir $run.results_dir
```

To choose a specific output path, pass `--output-dir` with a path that does not yet exist and is outside this package. Never point it at the retained package. `verify.py` without arguments verifies the originally retained bundle only; `--results-dir` also checks the newly generated external run.

The harness AST-executes only the frozen command helper and parser-option declaration; it does not import the controller's runtime dependencies or launch a session.

The original experiment freeze remains pinned to `e627b895`; before this reproduction fix, all seven frozen source Git blobs were independently compared with current main `674a0b3` and matched exactly. The historical candidate/result files were not regenerated or replaced.

## Replay-safety regression

`python -B -m unittest test_run_modes_safety.py` verifies that a fresh external run passes `verify.py`, that rerunning into the same destination is refused, package-internal output paths are refused, low-space paths are refused before creation, and all retained bundle hashes remain unchanged. This host has 0 bytes free on C:, so the test was run with `TEST_TEMP_ROOT=D:\CodexResearchTmp`; the two default-temp attempts stopped after candidate/audit completion when the C: temp volume could not hold the external bundle. Those stops are retained in `STOP-local-temp-first-attempt.txt`.

The earlier Windows newline-comparison failure is retained in `DEVELOPMENT_FAILURE_01.txt`; it was a runner-format issue, and the candidate's retained stdout files were unchanged.
