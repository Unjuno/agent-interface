# A18 retained-raw boundary audit

Related: [#5156](https://github.com/Unjuno/agent-interface/issues/5156),
[#59](https://github.com/Unjuno/agent-interface/issues/59),
[retained A18 delivery #6625](https://github.com/Unjuno/agent-interface/pull/6625).

## Result and adoption decision

The unchanged A18 auditor accepts eight targeted corruptions of its retained raw:
events outside the candidate window, admission after release, reversed sequential
two-key release timing, foreign teardown owner, foreign teardown intent,
cancellation cleanup before admission acknowledgement, Boolean activity count,
and floating activity count. This is `FAIL_AUDITOR_BOUNDARY_COVERAGE_SCOPED`.
The retained original is accepted and the two existing bracket/keymap negative
controls are rejected. No assertion that the original live raw is incorrect follows.

The additive `boundary_audit.py` composes with the unchanged validator, accepts
the original control, and rejects all ten negative controls:
`PASS_SUPPLEMENTAL_BOUNDARY_CONSTRUCTION_SCOPED`. The separate independent
auditor reads each emitted JSON and establishes its specific contradiction and
hash without importing either validator, the candidate, or mutation generator.
It passes all eleven rows with zero errors. Adopt these added checks as a
reviewable research audit supplement before using A18 chronology/identity in a
future live bridge; runtime promotion and a future live allocation remain separate.

## Execution and provenance

One pinned WSLc construction ran on 2026-10-03, 09:44:54–09:44:55 JST
(00:44:54.870999–00:44:55.429413 UTC). Candidate PID 8, auditor PID 9;
each invoked once, each exited 0; retries 0. This is a new mutation construction,
not an invocation of the consumed A18 candidate or formal auditor CLI. It calls
the retained pure audit function on copied data. No X11, GPU, input, game, model,
provider, image pull, installation, or shared-daemon change occurred.

The cached image ID is
`sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`;
Python 3.12.14, linux/amd64, kernel 6.18.40.1-microsoft-standard-WSL2.
Network was disabled; source mounted read-only; dedicated output mount;
CPU 0.5 and 128 MiB requested. WSLc reported unsupported swap limits / memory
limited without swap. Effective CPU/memory limits were not independently measured.
`os.cpu_count()` returned 12; that is host-visible topology, not proof of a quota.
The owned container was removed by `--rm`; post-run inventory was empty.

Freeze base is `11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d`, also confirmed as
remote main immediately before C01. `retained/audit.py`, `retained/FREEZE.json`,
and `retained/raw.json` are exact Git bytes from
`research/live_control/owner_keyup_xvfb_5156_a18_20261002/` at that base.
Original raw SHA-256:
`0db56f8f3560b2a76aec0aeffe728586533b5b95a82a19cee3c425ff99eddf2e`.
`FREEZE.json` pins the inputs and program bytes; `SHA256SUMS.txt` covers the
additive deliverable except itself. All historical A18 files remain unchanged.

The host diagnosis preceded the run: the retained six-mutation self-test passed;
the new regression had eight failing subcases before implementation and passed
all eleven subcases after implementation. See `construction/` and `PREREG.md`.
The eight controls are targeted, known counterexamples; no blind detection rate
or unseen-input generality is estimated.

## Scope and limits

Global containment checks only observation/event timestamps on this candidate's
monotonic clock, not future lease deadlines. Cancellation's recorded request time
is sampled after the flag is set, so cleanup onset is bounded from admission ack,
not from that later request sample. The cancellation teardown legitimately carries
null intent after autonomous cleanup; it is checked against that expected state.
The supplemental checker is scoped to the fixed A18 shape; it is not a new general
schema validator or a replacement for authenticated backend provenance.

A18 retains keymap booleans, not the full bitmap: this audit cannot reconstruct
lost witness bytes or establish server-state authenticity. A component/raw audit
PASS is not continuous physical occupancy, application receipt, independently
useful feedback, MAP01 success, a safety rate, human tempo, or a latency advantage.
The parent Issues remain unresolved. Main application needs FINAL-v5 content votes
and current-base integration verification; PR creation alone is not integration.

## Reproduction

From this directory, run the local regression:

```sh
python -B -m unittest -v test_boundary_audit
```

For a fresh explicitly separate construction output (never reuse C01):

```sh
python -B run_once.py /path/to/new-output-directory
```

`results/host-argv.json` records the original WSLc argv with only personal host
mount locations replaced by `<PACKAGE>` / `<RESULTS>`. `PUBLICATION.json` records
the original host-argv digest. Resolve those placeholders to this package and its
results directory. Public red-test traceback paths are likewise replaced by
`<package>`; trailing whitespace in its progress line was stripped. The original
host logs remain outside the published package.
Candidate/auditor output, generated raw cases, hashes and execution receipts were
not rewritten. Programmatically reusing this research supplement must keep its
scope restrictions and retain a separate run identity.
