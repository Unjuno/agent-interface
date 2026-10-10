# V39 per-key measured-release scorer-tail A01 report

**Disposition:** Construction PASS; independent audit V2 PASS. The first
independent audit returned `FAIL_AUDIT` because it rejected an omitted
top-level authority flag whose schema default is false. That first result is
preserved in `AUDIT.json` / `AUDIT_ATTEMPT_V1.json`; audit V2 corrects the
checker and retains the original failure. Two V2 parser attempts are also
preserved.

The strict V3 adapter joined the frozen raw `input_admission` and
`input_release_measurement` events without renaming either. The pair had exact
program, step, key, owner, intent and actuation identities, a confirmed
physical-up interval, and no remaining backend-held key. The adapter's
post-release boundary equaled the physical-up interval's upper endpoint,
`87811364949416`.

The measured-tail socket test returned `command_ready` with zero tail samples;
the normal iterator later delivered the pending command exactly once. V18
compatibility and V19 composition tests passed as well. Ubuntu WSL ran 43 core
tests. Windows CPython 3.11 ran 46 focused tests; one pre-existing anonymous
pipe test was skipped because `select()` cannot wait on Windows anonymous
pipes. WSLc was not installed; no container was required for these source,
JSON-schema, and socket constructions.

The core result extends the legacy receipt-shape checks in scorer-tail A01/A02
and the command-readiness construction A03: those used the old transition
receipt schema, while this run tests the V39 per-key measured-up schema through
the opt-in session composition. The repeated socket readiness assertion is a
compatibility regression for the refactored shared sampling loop, not a new
readiness-performance claim.

This does not test an X11 server, ViZDoom, a live planner, OS input, application
consumption, independently useful feedback, threat response, bounded recovery,
or task effect. The session tail runs during final cleanup; it does not establish
feedback quality during frontier-model latency. The #59 live threat-control
gate remains open.

Commands, pre-run hashes, exact test outputs, audit attempts, and the final
independent audit are retained in this directory. `SHA256SUMS.txt` covers the
post-run result and audit artifacts.

The PR workflow checks were also run locally against this checkout: the
research workspace unit suite passed 22 tests on Windows CPython 3.11, the
workspace index CLI indexed 159 top-level research directories, and the
Ubuntu WSL replay-gate suite passed 2 tests. The workspace index CLI was run on
Windows because WSL Git cannot resolve this Windows worktree's `.git` pointer;
that WSL invocation failed with `GIT_COMMAND_FAILED` and is retained alongside
the successful host run. These checks validate repository consistency and
replay determinism, not live gameplay or the open #59 control gate.
