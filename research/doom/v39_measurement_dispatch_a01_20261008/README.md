# V39 measurement-session dispatch construction A01

## H / T / D / C / U

**H.** Current-main V39 has an explicit `--measurement-session` switch. With the switch, the exact `session_command` should select `session_map01_v15.py`, and the run report should label the mode `v15_scorer_only_per_key_release`. Without it, the command should preserve the V12 default and report `v12_default`. The selected V15 source chain should contain the per-key release instrumentation. This checks a future-run dispatch contract; it cannot repair or reinterpret a historical run.

**T.** Freeze current main and seven source blobs. AST-execute the exact V39 `session_command` with the exact parser option extracted from `main`, evaluate the exact report's measurement label expression, and trace the V15 session's release backend to the transition owner and V12 key owner. Run normal and optimized modes, plus independent output reconstruction and mutation controls. Do not start the session, game, model, GUI, container, or input path.

**D.** PASS only if both CLI states parse as frozen, default and measurement commands choose V12 and V15 respectively, all other session arguments are preserved, labels match the chosen path, and the V15 release source chain contains the pinned per-key timing fields. Any mismatched mode/path/label or source identity is FAIL.

**C.** The past V39 run's source manifest showed V12 without the V15 overlay. This construction result does not prove what arguments its absent launcher passed, and the report label is generated only after the live run proceeds.

**U.** This verifies the current command-construction seam and source capability only. It does not establish runtime launch selection, physical key state, useful feedback onset, recovery, task effect, threat response, or MAP01 outcome. A fresh V39 threat exposure remains separately gated.

## Result

The exact current-main helper selects `session_map01_v12.py` for the default parser state and `session_map01_v15.py` when `--measurement-session` is present. The report label follows the same flag in both cases. The selected V15 composition imports the owner-thread release backend, which composes release backend V2 and transition owner V4; transition owner V4 delegates to InputOwner V12, whose release receipts include per-key attempt and interval fields. Normal and optimized outputs match, and the independent auditor rejects path and label mutations.

## Reproduce

From the repository root run this read-only reproduction:

```sh
python -B research/doom/v39_measurement_dispatch_a01_20261008/run_modes.py
python -B research/doom/v39_measurement_dispatch_a01_20261008/verify.py
```

All execution is offline and synthetic. The harness AST-executes only the frozen command helper and parser-option declaration; it does not import the controller's runtime dependencies or launch a session. `run_modes.py` compares fresh stdout and independently reconstructed audit data against the retained raw files and refuses mismatches; it never writes over `RESULT.json`, `AUDIT.json`, stdout captures, or their manifest.
