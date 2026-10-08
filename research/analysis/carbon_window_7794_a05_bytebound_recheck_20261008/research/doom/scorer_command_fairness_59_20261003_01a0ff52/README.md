# #59 scorer command-service counterexample and proposed repair

**A01 first outcome: audit FAIL, preserved.** The retained main functions starved
an already-readable finish command in all 12 sustained-overrun cases. The first
patch restored eventual service in all 18 cases, but the stdin adapter sampled
twice before returning finish in six cases. The frozen raw-only oracle required
delivery after the first sample and rejected those six rows (18 error records).
All ten corrupted-raw controls were rejected. Do not call A01 a PASS.

**Ordinary repair v2: regression PASS.** Delivering an already buffered line
before sampling again fixes the remaining extra-sample path. A separately kept
red regression fails on six first-patch rows; the v2 green regression passes all
18 literal cost/component conditions, delivering the exact finish once after
one completed sample and keeping callbacks on the owner thread. Existing 32
polling/adapter/progress-clock tests also pass. This is engineering evidence
after A01; it does not replace, pool with, or rerun its formal candidate.

## What ran

- Exact source base: `cb13a10dce358649458f5aea00947b8aa43fc5b8`.
- Pre-execution freeze commit: `b9217982d0` (full identity in `results/A01/RUN.json`).
- Host: macOS arm64, CPython 3.14.5, standard library; injected 100 ms clock
  period, inert already-readable command and deterministic callback costs.
- A01: 36 rows, candidate once, raw-only auditor once, retries zero.
- Retained: six finish-served controls, 12 diagnostic-budget terminations after
  eight completed samples and zero readiness probes/reads/commands.
- First fair patch: 18 finish-served rows; stdin overrun returns after two
  samples rather than one. The original audit is unchanged and failed.
- Engineering v2: two regression methods (20 subcases), plus 32 existing tests.
  No second formal allocation. `engineering/green-v2.raw.jsonl` keeps the 18
  first-sample-service traces; `sources/fair_v2/` and `SOURCE_V2.json` pin the
  proposed source copy. The deployed v1 source/session is unchanged.

## Evidence and verification

| Artifact | Role |
|---|---|
| [PLAN.md](PLAN.md), [FREEZE.json](FREEZE.json) | Prospective H/T/D/C/U, matrix, source hashes, no-retry gate |
| [sources/source-map.json](sources/source-map.json) | Exact main blob IDs and SHA-256 |
| [results/A01/raw.jsonl](results/A01/raw.jsonl) | First candidate traces |
| [results/A01/audit.json](results/A01/audit.json) | Original failed raw-only audit and ten controls |
| [results/A01/RUN.json](results/A01/RUN.json) | Actual UTC command/exit/log receipts and invocation counts |
| [development/](development/) | Initial two-component red, first green, import-layout failure and repaired 32-test result |
| [engineering/](engineering/) | Extra-sample red, v2 green traces/receipts and proposed patch |
| [SHA256SUMS](SHA256SUMS) | Deliverable byte manifest; excludes itself |

Development/engineering stderr copies replace the author's absolute workspace
prefix with `PACKAGE` only. Separate provenance files retain original and public
hashes; original unredacted transcripts remain in the author's private work
folder. A01 raw/receipts are not redacted. The raw field `pending_bytes` is an
assay naming error: it counts pending chunks (0 or 1), not byte length. Audits
use it only as the pending-command sentinel; no byte-capacity claim is made.

From this package directory:

```sh
FAIRNESS_VARIANT=fair_v2 python3 -B -m unittest test_fairness test_first_sample_delivery -v
PYTHONPATH=sources/fair_v2 python3 -B -m unittest discover -s sources/regressions -v
```

Historical red test defaults and source snapshots are deliberately excluded from
pytest automatic collection by this package's `conftest.py`; explicit commands
above are the construction entry points. There is no workflow/runtime import of
this package, no runtime replacement, and no automatic candidate invocation.
The frozen audit may be rerun on retained raw into a fresh *scratch* output to
verify its original FAIL; never reuse `results/A01/audit.json` or rerun candidate.

## Decision and limit

The persistent-cost source recurrence in PLAN establishes why the retained
sample-then-continue path can starve input indefinitely. The eight-sample trace
is a bounded witness, not a timing guarantee. The smallest proposed remedy
services ready input between samples and prioritizes buffered complete lines.
Scorer-thread ownership and command-content isolation are retained in the tested
cases. A blocked/nonreturning sample still blocks both versions; command floods,
real I/O overhead, cancellation during a callback and real-game task effects are
unmeasured. No model/container/GPU/GUI/input/live allocation was used.

**Adoption: HOLD pending independent review and separately frozen integration.**
The proposal is a concrete repair candidate for #59's finish/command-service
readiness, not a live threat-control result, release guarantee or MAP01 exit.


## Newly confirmed terminal-accounting limitation

The v2 source still underreports final missed periods after a returning sample
or sink overrun followed by FINISH/EOF/cap. [New ordinary diagnostic evidence](terminal-accounting/README.md)
preserves ten overrun witnesses and ten fast controls with separate saved-record
grid reconstruction. Original A01, the first FAIL and all prior engineering
raw/source remain unchanged. Command-service regression PASS does not establish
accurate terminal statistics or the full measurement gate. This is a known-fault
research archive; runtime adoption/repair remains separate at PR #6913.
