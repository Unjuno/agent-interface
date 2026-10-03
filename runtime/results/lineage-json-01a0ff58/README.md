# Lineage canonical JSON identity — #57

The public lineage wrapper previously delegated when a receipt, sidecar,
program or current runtime value differed only by Python's equal-valued
integer/float/boolean comparison. The existing canonical JSON serialization
now governs these identity checks, matching the representation used by the
lineage digests. This is an ordinary engineering repair.

Worker `01a0ff58-8f42-73c3-857d-35a2636e7bd3`, FINAL-v5.
Base `3116528f3abe0fec72cfc1b5b2b5b4b05538512e`.
Parent [#57](https://github.com/Unjuno/agent-interface/issues/57),
historical freshness boundary [#2428](https://github.com/Unjuno/agent-interface/issues/2428).
Branch `worker/01a0ff58-8f42-control-boundary`.

## Hypothesis and prospective decision

H: canonical JSON identity refuses differing numeric representations before
delegation while preserving digest refusal, freshness/mismatch precedence,
key-order-insensitive identity, valid delegation and input immutability.
T: test-first regression; prospective 116-case corpus (14 single-field
locations × eight JSON values, one key-order control and three digest
controls); exact baseline/candidate source copies; inert dispatch callback;
separate recursive type-sensitive raw-only oracle and six corruption controls.
D: the baseline must expose the reproduced gap; candidate must exactly
match the independent oracle for every frozen case, leave inputs unchanged,
and retain existing scoped regressions. Missing coverage or effective-control
failure is HOLD/FAIL, never an excluded row.
C: full native dispatch may independently reject some malformed values;
this does not prove a live authority bypass. Identity comparisons do not
replace the core program validator.
U: only the specified parsed JSON values are covered. Original JSON spelling,
duplicate object members, arbitrary Python objects, concurrent mutation,
authentication, clock trust, native input and application effects are excluded.
Serialization overhead and performance were not measured.

## Observed result

- Test-first: eight test methods, ten failing subcases (`red.log`), exit 1.
- Repaired: the same eight methods pass (`green.log`), exit 0.
- Frozen matrix: baseline 28/116 oracle mismatches; candidate 0/116.
  Both arms ran in one input-free host invocation (`raw.json`), exit 0.
- Separate raw-only audit: `PASS_JSON_IDENTITY_SCOPED`; all six copied-raw
  corruptions rejected (`audit.json`), exit 0. This auditor was implemented
  by the same author and does not substitute for non-author content review.
- Existing CLI workflow command plus lineage regressions: 129 methods,
  123 pass / six platform skips, exit 0 (`cli-ci-01.log`).
- Core discovery: 65 methods pass, exit 0 (`core-ci.log`).
- Optimized Python lineage regressions: eight methods pass, exit 0.
- Existing CLI doctor returned exit 0, diagnostic authority false.
  Compilation and final diff checks are recorded in `validation.json`.

The historical #2428 workflow's retained test fixture separately fails two
methods on both exact baseline and repaired source. It changes the receipt
and rehashes it, but keeps the sidecar's old `evidence_receipt_digest`, so
the earlier `EVIDENCE_DIGEST_MISMATCH` refusal correctly precedes the expected
STALE_* assertion. The valid-control method passes. Both original logs are
retained (`historical-baseline.log`, `historical-regression.log`); neither
historical fixture nor digest/error precedence was changed to make this green.
The current `test_lineage_freshness.py` provides correctly linked stale controls.
Hosted/cross-platform results are separate and are not claimed passed.

The initial sparse checkout required local construction repairs and source
closure before package imports worked. Its first checkout/import failures
remain in private tool/scratch records; no failure is a scientific outcome.
Only this task's isolated restore process was stopped and its known stale
index lock preserved outside the repository. No other worker or shared
runtime was stopped or changed.

## Reproduction and preservation

Run from the repository root:

```powershell
python -m unittest -v runtime.cli_v1.test_lineage_freshness runtime.cli_v1.test_lineage_json_identity
python -m unittest discover -s runtime/core_v1 -p 'test*.py'
```

For matrix reconstruction, copy this package to a fresh scratch directory,
then run `python run_matrix.py` and `python audit.py` there. Preserve the
retained original raw. `construct.py` documents corpus construction; do not
use it to overwrite the original freeze or reinterpret its first outcome.
The runtime source copies are `.txt`, and this results directory is outside
runtime imports/test discovery. This change adds no workflow or formal run.

`freeze.json` binds prospective corpus, exact source copies and both checker
implementations; `SHA256SUMS` binds the published package except itself.
Baseline bytes equal the Git blob at the named base; candidate bytes equal
the modified production source. Matrix UTC boundaries, Python and Windows
identity are in `raw.json`. No physical latency result is claimed.
Public regression logs replace the private checkout prefix with `<workspace>`;
original bytes/hashes remain privately retained and are listed in
`publication.json`. Matrix, corpus and frozen source bytes remain unchanged.

## Delivery boundary

Shared WSLc HOLD remains unresolved. No WSLc/container/VM, GPU, GUI, model,
physical input or consumed formal allocation was used. Same-type invalid
programs remain subject to normal core admission. Broad #57 efficiency,
live reliability and human-tempo gates remain open.

Non-author FINAL-v5 committee/content approvals, current-base combination
verification and conditional main application remain outstanding. An
authenticated read reported main `Branch not protected` and an empty ruleset
list on 2026-10-03; these conditions must be refreshed at actual application.
No merge/apply lock is held. Fleet N and common deadline are unavailable to
this session; no global deadline or worker count was reset.
