# Rescue of #6924: private-pipe service and terminal-accounting boundary

Preserve all 57 original packet files (56 manifest targets) byte-for-byte from
`17af2d061012721bde0efd778c07cd9d1e8f2ea4`, branch
`research/scorer-private-pipe-01a0ff52-93c2-20261003`, delivery PR #6924.
Original packet: `research/doom/scorer_private_pipe_59_20261003_01a0ff52_93c2`.
Complete original history is retained at annotated tag
`archive/recovered/pr6924-source-17af2d0-20261004` before branch retirement.

## Fresh retained-data verification, 2026-10-04 JST

Run `python -B runtime/results/scorer_private_pipe_rescue_6924/test_archive.py -v`.
All three tests pass on macOS CPython 3.14.5 and bundled CPython 3.12.14.
They check every original Git blob and manifest hash, all 17 frozen inputs,
six historical source-copy Git/size/hash witnesses, public/private projection
maps and original receipt stream bindings, the development first-auditor exit1,
and the one-producer/one-auditor/zero-retry historical execution counts.
Normal and optimized Python explicitly execute only the raw-only auditor and
copied-raw controls, writing new results exclusively in fresh private temporary
directories. Full 60-row audit JSON matches the retained result. All 12 copied
corruption hashes and refusals match; only the first diagnostic of reordered rows
is permitted to select any actually changed case field, because the unchanged
oracle iterates a Python set. Every other diagnostic is exact. The first rescue
test attempt failed by demanding a deterministic diagnostic: current rejection
was `case field index`, historical rejection `case field adapter`. This is a
qualification of diagnostic order, not a weakening of ordered coverage or a
change to the original control output.
Independent arithmetic reproduces all 16 posthoc counterexamples exactly:
at least two full 20 ms boundaries elapsed before FINISH while archived v2
reported zero missed periods. The prospective service gate remains PASS_SCOPED;
the recorded withdrawn runtime approval and UNEXECUTED full measurement gate
remain unchanged. No candidate, runner, scheduler copy, OS-pipe producer deck,
consumed trial, model, game, GUI, or physical input is repeated by archive tests.

## Current-main implementation is preserved

#6913 is now MERGED (2026-10-03T06:40:45Z), final head
`9a9542438d5bee663b59170ee00fe43aff84e213`. The current main polling/stdin modules
match that final head and include the later terminal missed-period accounting;
they must not be replaced by this packet's older `8f587287...` source witnesses.
No production source is changed here. A fresh local normal/-O run of
`test_main_thread_scorer_polling_v1`, `test_map01_scorer_stdio_adapter_v1`, and
`test_scorer_command_service_01a0ff58` passes 23 tests per mode from
`research/doom`. This includes terminal FINISH/EOF/sample-cap and no-double-count
regressions, plus a fake-session composition, not a formal real-game experiment.
The first root-package invocation of the first two modules produced two import
errors because their imports require the documented `research/doom` working
directory. Correcting the command's directory, not production code, passed17
tests, then the full three-module selection above passed23 in each mode.

## Historical scopes retained

Retained loaded16 rows are censored after four completed samples with FINISH
unread, not infinite runs and not completed-command latency. V2 serves all24
rows after one sample; read-first serves12 with zero initial observations and
does not exercise the requested scorer load. It changes the observation contract
and is not adopted. Fixed alternating order, four repetitions, recorder overhead
and returning sleep load establish neither real-time bounds nor task benefit.
Private original logs remain historical private custody, not newly independently
inspected bytes; their public derivatives retain explicit distinct hashes.
Initial development RED and both prospective freezes remain unchanged.
No Linux/container result, live measurement integration, human-tempo usefulness,
independent content vote or closure of #57/#59 is claimed. This rescues useful
evidence and its counter-interpretation; it does not revive an old approval.
Only after ordinary PR integration, exact main equality, remote tag readback and
fresh ref/dependency checks may the superseded delivery refs be retired.
