# Backend factory admission repair — #6856

**PASS_FACTORY_ADMISSION_SCOPED**, ordinary engineering regression and finite
contract characterization. Base main: `11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d`.
No formal research allocation was consumed. Main application is pending review.

`BackendRegistry.create()` previously returned a backend with a valid probe even
when observation, execution, or input release methods were missing/noncallable.
Require all four `PlatformBackend` methods to be callable before probing. Preserve
the existing probe-result and unavailable-support checks. Registry discovery via
`probe()` retains its existing behavior; this repair governs creation for use.

## Decision and evidence

- H: a factory product must implement the callable mechanical interface before
  the registry returns it as a usable backend.
- T: baseline/red regressions, a three-state finite product over four methods,
  repaired/green regressions, and separate raw-only reconstruction.
- D: admit only the complete interface, refuse all incomplete products with
  `ContractError` before probe, and never invoke observation/input/release.
- C: annotations are not runtime admission; Protocol attribute presence alone
  does not establish callability. Fixture methods deliberately raise on I/O.
- U: callable methods do not prove signatures, method return contracts, truthful
  capabilities, physical release, native OS support, scheduler/thread safety or
  task effects. This is not current public MCP or GUI evidence.

Existing kernel tests passed 18/18 before repair. The new regression's 20 invalid
subcases produced 15 missing-rejection assertion failures and 5 wrong-boundary
exception errors; the complete positive passed. The captured second red run is
`red.*`; the earlier same-result console run is recorded on #6856. After repair,
kernel discovery passed 21 test methods (including the 20 invalid subcases).

The finite matrix independently varies `probe`, `observe`, `execute` and
`release_all` across missing/noncallable/callable: 81 combinations. Baseline
accepted 27 products, of which 26 were incomplete, and raised AttributeError or
TypeError for the remaining 54. Repaired creation admitted the one complete
product and rejected 80 incomplete products with ContractError before probe.
Observation/input/release calls were zero in both matrices.

The independent raw-only `audit.py` imports neither registry nor generator. It
checks all ordered rows, decisions, exact integer call counts, source snapshots
and six copied-output corruption controls: omitted row, duplicate row, reversed
admission, extra probe, release invocation and boolean count. All six reject.

The first matrix harness attempt and first audit attempt both exited 1 because
their evidence-source path calculations were one parent too high. These are
retained in `baseline-matrix.*` and `audit.*`. The harness was corrected and
ordinary construction checks were rerun into new filenames `baseline-matrix-02.*`
and `audit-02.*`. No historical/formal allocation was rerun or overwritten.

Each command's UTC start/end, exit code and output sizes are in its receipt.
Windows host CPython 3.11.9, stdlib only; one tiny process at a time. No model,
GUI/input, WSLc/Docker, GPU or shared-resource lease. No timing/performance claim.
Common fleet deadline was not established by this worker; no deadline is reset.

## Reproduce

From repository root:

```powershell
python -B -m unittest discover -s runtime/kernel -p 'test_*.py' -v
python -B -m compileall -q runtime/kernel
$env:PYTHONPATH = (Get-Location).Path
python -B runtime/results/backend-protocol-01a0ff35/matrix.py
python -B runtime/results/backend-protocol-01a0ff35/audit.py
git diff --check
```

The matrix command prints new regression output; it does not overwrite captures.
Audit consumes retained baseline/repaired output. Exact source capture bytes are
preserved with `-text` attributes; working source comparison permits only LF/CRLF
representation changes. `MANIFEST.json` pins retained artifact bytes.

Local absolute paths in published traceback logs are replaced with placeholders.
REDACTION.json identifies affected files, original/published hashes and the exact
replacement; original logs remain private on this host. No raw matrix semantics
or source snapshots were redacted. Receipt byte counts describe original output.

The CI entry changes only from one explicitly named kernel test module to kernel
test discovery, so the new regression is included on its existing OS matrix.
Local compile/discovery/diff checks passed; hosted CI is not claimed passed.

## Integration handoff

Dedicated worker/branch/path are recorded on #6856. No changes to #6852/#6853's
lifecycle or test module. FINAL-v5 requires a committee fixed before votes,
two explicit non-author content approvals, non-author combined-tree verification
and conditional main application. No committee/approvals/application occurred in
this work. No shared input/resource/merge lock is held. Preserve this repair for
review; a tested PR is not overall computer-control goal completion.
