# Formal GTK/X11 result — #3518

## Disposition

**HOLD for the full formal GUI gate.** The policy-count and GTK-title sub-gates passed their independent fixed oracle, but allocation #02 has material evidence gaps: the runner's embedded ID says #01; full-screen pixel hashes differ in only 17/32 rows; raw image captures are not retained; and process termination/cleanup is performed with `terminate()+wait()` but its exit/PID evidence is not recorded in the ledger or independently audited. Do not treat this as a formal GUI PASS. The first registered attempt (#01) stopped before any row because of a Docker ENTRYPOINT invocation error; it was retained and not retried. Successor #02 ran once and yielded 32/32 rows; no retry/tuning was done. Attribution rests on the #02 preregistration, exact unchanged source hashes, the sole subsequent Docker execution, and these explicit deviations; do not silently relabel the raw log.

## Result

OrbStack Docker image `agent-interface-2972:20260920`, image ID `sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27`, linux/arm64, `--network none`, source read-only, one GTK/Xvfb process pair per row. 8 fixed traces × 4 policies = 32 rows. All 32 rows verified Space key release. The candidate's transport counts in case order were 1,1,0,0,1,1,1,1; GTK title task-effect counts were also 1,1,0,0,1,1,1,0 (effect-off case). This supports the narrow hypothesis that a later revoke does not retroactively erase an earlier emission; revoke-first, replaced-target stale observation, stale sequence, duplicate rising edge, and restart replay are handled as preregistered. The three controls exhibit the preregistered unsafe/order-sensitive behaviors.

Independent fixed-oracle audit: PASS, exact 32-row matrix, expected counts, positive-observation action indices, GUI title/effect-off classification, and key-release evidence. It imports no candidate code.

## Important qualification

Only 17/32 before/after X11 root-image hashes differed, although 24 rows recorded a positive GTK title/count effect. The full-screen pixel-delta field is not a reliable per-row GUI-effect witness under this capture timing. The independent audit verifies recorded hashes are self-consistent, not that pixel delta should equal task effect. GTK title/count readback supports the narrower fixture-state observation only. Raw before/after images and process exit/PID cleanup evidence are absent; these gates are **not passed** and require a newly preregistered successor capture implementation.

No real Codex GUI, MCP event stream, model, user task, accessibility path, latency, safety, production reliability, or task success was tested. Historical #3511/#3508 evidence is unchanged.

## Artifacts and integrity

- Raw rows: `evidence/rows.json`, SHA-256 `8a43ea97920de3a9918ffd56520c4977a76d8334444337a4b556b3583ef242b2`.
- Independent auditor: SHA-256 `1235ff9a9655d42858ca931239098593ed123ae177d9a25ca2be38eeb5ab625b`.
- Runner: SHA-256 `5ee6875b4f7e75adb655e989183bb0b660fbf3d4f3d9773b0114a3ccc5887bc6`.
- Fixture: SHA-256 `ea8e0cd5586c243a2de65a86c8ba1258c3f804dc319ee6d36ecf4c59770d98fe`.
- Allocation #01 stop record is retained at `STOP-allocation-01.md`.
