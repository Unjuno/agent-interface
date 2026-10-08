# Revision 2: teardown witness consistency repair

Read this correction together with the historical C01 `../REPORT.md`. The C01
outcome remains valid for its declared controls, but its recommendation to use
the supplement in a future live bridge now requires these additional gates.
The frozen v1 supplement alone is HOLD for teardown witness consistency.

Independent review [5964127751](https://github.com/Unjuno/agent-interface/pull/6865#issuecomment-5964127751)
reported 15 copied-raw contradictions accepted by v1: appended owner/intent/time
disagreements for the single and two-key cases (six), teardown verification
outside its caller bracket (six), and a within-bracket receipt time disagreeing
with the final owner witness (three). Local reproduction confirms all 15.
Four further structural controls expose absent appended capture, duplicate
final witness, changed final witness, and an extra appended field.

`teardown_audit.py` composes with the unchanged v1 supplement. It checks integer
verification time inside the caller bracket, exactly one final snapshot equal
to the receipt after removing its two caller timing fields, and exact appended
capture equality for single/two-key teardown. The cancellation teardown has no
appended capture in the historical A18 shape; it still needs a matching final
witness. The original candidate's capture semantics were checked in Git source.

## Ordinary engineering verification

On native Windows 11 / CPython 3.12.10, one regression method covers 30 subcases:
one original positive, ten prior negative controls, 15 reviewer negatives, and
four structural negatives. Before repair it exited 1 with 19 failed subcases;
after repair it exited 0 with all 30 matching the expected accept/refuse outcome.
Actual command start/end, exit status and source hashes are retained in
`verification/red.json` and `verification/green.json`; stderr/stdout are kept.
Only private traceback directory prefixes are replaced with `<package>`.
Test wall time is not an input/GUI latency measurement.

This is ordinary local construction/regression, not a new formal allocation.
No C01 wrapper, candidate, independent auditor CLI, A18 live process, backend,
input, model, GPU or container was run. C01's ten frozen files and all 45 files
covered by its historical manifest remain byte-identical. The historical
manifest continues to describe that original delivery; `../REVISION2-SHA256SUMS.txt`
separately covers this additive revision except its own manifest.

## Scope and decision

Adopt v2 as the proposed research audit entry point within the fixed A18 shape,
pending non-author review and FINAL-v5 main application. The frozen v1 remains
for reproduction of C01 only. Do not use the old C01 runner to claim v2 validation.
This repair checks internal consistency of recorded JSON. Coordinated fabrication,
authenticated provenance, arbitrary schemas, thread races, physical release,
application effects, useful feedback and MAP01 efficacy remain unestablished.
Existing Windows workspace fixture failures remain disclosed in `../CI.md`.

The fields `release_call_started_ns`, `verified_ns`, and
`release_call_returned_ns` are integer nanosecond readings of A18's same monotonic
clock; their SI quantity is time (seconds), stored as integer nanoseconds. The
caller start is no later than verification, which is no later than caller return.
The copied negative readings are authored counterexamples, not new measurements.

From the package directory:

```sh
python -B -m unittest -v repair_v2.test_teardown_audit
```

No runtime, workflow, common checker or original live evidence was modified.
