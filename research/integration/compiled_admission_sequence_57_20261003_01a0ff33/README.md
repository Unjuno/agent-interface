# Compiled admission sequence boundary — #57

Bounded engineering repair under FINAL-v5, worker `01a0ff33-b04b-7b51-8194-a60b82fed8a2`,
Windows host, 2026-10-03. Intake/review base: `11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d`.
Patched runtime/test source commit: `727b130ec5182c10e0cc23bbe6efccfa5dd80bed`.
Ownership and prospective H/T/D/C/U were recorded on
[#57 before repair](https://github.com/Unjuno/agent-interface/issues/57#issuecomment-5963769409).

## Problem and change

The existing compiled runtime compared admission `expected_sequence` to its exact-integer
observation sequence with Python value equality alone. A boolean, float or integer subclass
could therefore reach the execution adapter despite not satisfying the observation's exact
integer contract. This is a reproduced direct adapter-boundary defect; no physical input or
downstream exploit was demonstrated.

One exact-type check now rejects malformed equal-valued sequences before dispatch. Existing
integer matching, ineligible-refusal precedence, deadline handling, verified action prefix,
and one-use native admission remain enforced. Invalid eligible admission keeps the existing
`ValueError` contract and caller-owned cleanup duty; no new receipt/error policy is introduced.
No core `contract.py`, kernel lifecycle, backend, MCP schema, default or workflow is changed.

## H / T / D / C / U

- H: an eligible compiled admission requires an exact Python `int` equal to the current
  observation sequence; numeric aliases must never reach the execution adapter.
- T: six test-first regressions, an independent fixture calling the real runtime across
  five observation sequences, ten value kinds and three admission profiles (150 rows),
  and a raw-only oracle that imports neither runtime nor fixture. Ordinary engineering
  and finite analytical checks only; no formal allocation or consumed experiment rerun.
- D: every malformed eligible row has zero dispatches; matching integer controls complete;
  ineligible and expired controls preserve their existing outcomes. The retained baseline
  must remain failed, corrected rows must all reconcile, and corruptions must be rejected.
- C: a downstream adapter may already reject malformed sequences. The demonstrated boundary
  is direct `compiled_gui.run`, not proof of duplicate/stale OS input or a live vulnerability.
- U: finite fixtures, synchronous inert callbacks, no real backend, application, timing,
  model, resource-enforcement, general reliability, efficiency or human-tempo claim.

The observation set is 0, 1, 2, 7 and the largest signed 64-bit integer. The admission kinds
are matching/mismatched exact integers, false, true, numerically constructed float, string,
null, integer subclass, NaN and infinity. Raw JSON records nonfinite inputs by textual
representation and remains strict JSON. Profiles are eligible/current, ineligible/stale and
eligible/expired. The largest integer's float rounds upward, so that baseline float control
already refuses; it is retained in the denominator.

## Executed evidence

| Check | Result | Evidence |
|---|---|---|
| Existing compiled baseline | 29 tests pass | Original tool command, before edits |
| First regression | exit 1, four failing subcases | Original private transcript; first direct tool output |
| Recorded prepatch regression repeat | exit 1, same four failures | `checks/red-recorded-02/` |
| Independent before matrix / audit | 150 rows; 11 boundary violations, audit exit 1 | `before.json`, `before-audit.json` |
| Independent after matrix / audit | 150 rows; errors empty, audit exit 0 | `after.json`, `after-audit.json` |
| Compiled regression + existing graph | 35 tests pass | `checks/green-regression/` |
| Entire core suite | 71 tests pass, CPython 3.11.9 | `checks/core-suite/` |
| Entire core suite, optimized Python | 71 tests pass, CPython 3.12.14 `-O` | `checks/core-python312-optimized/` |
| First composition attempt | exit 1: two Xlib imports and one mcp import missing | `checks/composed-route/`; preserved infrastructure errors |
| Composition with private dependencies | 71 tests pass | `checks/composed-route-python312/` |
| Portable distribution | 9 tests pass | `checks/distribution-suite/` |
| Raw auditor controls | 5 tests pass normal and `-O` | `checks/audit-mutations/`, `checks/audit-optimized/` |
| Committed portable build + isolated import | bool/float refuse, integer completes | `checks/build-committed-archive/`, `checks/committed-archive-sequence/` |

The 11 baseline aliases are false at sequence 0, true at sequence 1, four equal floats,
and five integer subclasses. The repaired matrix has no malformed dispatch. Mutation tests
reject missing and duplicated rows, fabricated malformed dispatch, lost valid dispatch and
scope relabeling while keeping the baseline FAIL. The first RED output remains in the private
session; the published full RED log is an explicitly identified ordinary regression repeat,
not falsely labeled the first invocation. There is no formal candidate/auditor allocation.

CPython 3.12.14 was supplied by the bundled local runtime. A private virtual environment
adds mcp 1.30.0 and python-xlib 0.33 and inherits Pillow 12.3.0 / NumPy 2.3.5. These differ
from hosted native CI's Pillow 10.2.0 / NumPy 1.26.4, so local results are not reported as
identical CI execution. No display was opened by these inert adapter tests. Full native
protocol/harness CI, hosted cross-platform checks and live transfer were not run here.

The built archive pins the source commit above. Archive SHA-256:
`190de42a67a08078ed04ecf1cdc7469118cbeca238dceca6daf3991d9c17a73b`.
Its compiled module SHA-256 equals the tested after-source:
`ccaff4ce59cfbe7af76bfe80655c968eed7855acdb7514df64730790766cf7f7`.
The archive remains a local verification artifact; `ARCHIVE_MANIFEST.json` retains its
complete rebuild identities. No research module is imported by the isolated child.

## Reproduce

Use Python 3.12 with the declared test dependencies, from the repository root. These commands
are ordinary repeatable verification, not live input or a consumed experimental allocation.

```text
python -B -m unittest discover -s runtime/core_v1 -p 'test_*.py' -v
python -B -m unittest runtime.guarded_x11_v1.test_compiled runtime.cli_v1.test_mcp_guarded runtime.distribution_v2.test_compiled_archive -v
python -B -m unittest runtime.distribution_v2.test_distribution -v
python -B -m unittest discover -s research/integration/compiled_admission_sequence_57_20261003_01a0ff33 -p 'test_*.py' -v
python -B research/integration/compiled_admission_sequence_57_20261003_01a0ff33/probe.py --root . --output <fresh-raw-path>
python -B research/integration/compiled_admission_sequence_57_20261003_01a0ff33/audit.py <fresh-raw-path> --output <fresh-audit-path>
```

Build the committed zipapp through `runtime.distribution_v2.build`, then run
`archive_probe.py <archive-path>`. Both raw/audit writers refuse an existing output.

Public logs/receipts redact private absolute host paths. Original bytes and receipts are
retained privately, read back before deriving the public copies, and identified by their
original hashes in `PUBLICATION.json` and the public receipts. Raw matrix bytes are unchanged.
`SOURCE_SHA256.json` and `SHA256SUMS` bind source and published evidence without self-reference.
The initial staged evidence whitespace check failed on generated metadata CRLF, but a shell
sequence continued to local evidence commit `e6e982c68`. That unpublished attempt is retained
in branch history. Derived metadata was normalized to LF before publication; original log
bytes are retained with scoped binary diff attributes and explicitly added despite the
repository's generic log ignore rule. No execution, source gate or outcome was changed.

## Disposition and handoff

Retain the exact-type repair for review. The finite contract gate passes only the stated
boundary. #57's full integration/economics and #59's real-time-control goals remain open.
Shared WSLc HOLD was not resolved or bypassed. No container/GPU/model/GUI/input allocation,
main write, branch deletion or resource acquisition occurred. Own checks have terminated;
the dedicated branch/worktree and local raw originals remain available.

Main delivery requires FINAL-v5 nonauthor content consensus, current-main combination review,
actual required GitHub conditions and a conditional application path. Author verification
and this raw-only oracle are not nonauthor votes. No fixed reviewer committee or approval
is implied by this report; the actual review record belongs outside the proposed tree.
