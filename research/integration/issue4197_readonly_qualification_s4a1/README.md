# #4197 retained-evidence qualification — s4a1

**HOLD_HISTORICAL_INDEPENDENT_QUALIFICATION**. This is an append-only
engineering review of the existing evidence, not a new native experiment,
production vulnerability, scientific rerun, or runtime promotion.

## Findings

1. **Original source provenance recovered.** The existing published source
   archive contains the exact originally declared FREEZE and ENVIRONMENT bytes.
   All six embedded Python files match the original freeze. The outer FREEZE
   has equal JSON values with different formatting. The outer ENVIRONMENT also
   omits the inner `xvfb` diagnostic array. Those diagnostics report an unsupported
   `-version` invocation, not an Xvfb version. The preceding conversation's
   ENVIRONMENT_UNRESOLVED finding is therefore resolved by existing originals;
   no historical environment was regenerated or substituted.
2. **Historical construction delivery remains incomplete.** The published
   `construction.tar.gz.b64` has its expected Git blob identity but strict
   Base64 decoding returns `Incorrect padding`. The original bytes have not
   been padded, repaired, replaced or interpreted as an empty construction run.
3. **The original auditor has narrower coverage than previously claimed.**
   It accepts the unchanged historical raw and passes its original ten mutation
   controls. It also accepts all twelve newly frozen contradictory derivative
   records. The missing checks concern same-lifetime token consistency,
   geometry/byte counts, observer coverage, token/XID validity, row identity,
   and exact JSON boolean/integer distinctions. This is
   **FAIL_AUDITOR_SUMMARY_COVERAGE**, not proof that the historical GUI mechanism
   failed or that its scoped observation never occurred.
4. **Missing native data cannot be recreated by assertions.** The decodable
   source/raw portion retains capture digests, counters and summary flags rather
   than complete native pixel/event/process evidence. A source/raw hash match
   establishes byte identity against the anchor, not independent reconstruction
   of absent observations. Originals outside this inspected scope are unknown.

## H / T / D / C / U and actual execution

The full source-first plan is PLAN.md. H was that the exact retained auditor
rejects the twelve contract-inconsistent derivatives. T was one original input
plus those twelve well-formed JSON copies, then the ten original controls, using
only the reviewed archived stdlib audit scripts. D evaluates original-source
recovery, publication integrity and directed summary coverage separately. C:
source-guided controls are not a random corpus or natural failure-rate estimate.
U: no new independent native evidence, runtime adoption, model usefulness,
latency/token savings, cross-platform result or external human review.

The pre-run commit was `aea1c063aba35efac24673160909ec7a5d6c4c8e`;
FREEZE SHA256 `5965586e9c5afd42cd0e2a9729b115a084f2bad32069fb8ba8dd5bdec9c5faf9`.
All nine public file identities were read back before the retained invocation.
The unchanged historical raw is 12,593 bytes, SHA256
`b67790414851ebbe0ed82cb835eefc03b884ac89190d6d39040f004b416dd193`.

| Executed check | Result |
|---|---:|
| Pure pre-run construction methods | 6 passed |
| Original auditor input | PASS retained |
| Frozen contradictory derivatives | 12/12 incorrectly accepted |
| Original mutation controls | 10/10 rejected as before |
| Archived audit/control child processes | 14 observed exit 0 |
| Separately structured receipt checks | 164 checks, 0 errors |
| Post-result regression methods | 9 passed, including 8 negative controls |
| Native/GUI/actor/model calls | 0 |

The outer retained command and separate receipt check also exited 0; their
actual argv, PID and output identities are retained. Successful engineering
execution does not turn the coverage failure or publication HOLD into PASS.
No source/gate was tuned after the result; the supplemental regression file is
explicitly post-result and does not claim prospective status.

Environment: provided Linux x86_64 execution container, CPython 3.13.5,
standard-library saved-data processing only. No Docker/OrbStack image
attestation, package installation, external experiment network or performance
measurement. Process IDs are execution receipts, not authenticated incarnation
proof. The independent checker is separately implemented by the same author,
not independent human approval.

## Read-only reproduction

From this added directory with Python 3.12 or 3.13:

```sh
python -S -B restore.py --out /tmp/issue4197-s4a1-new
python -S -B reconcile.py /tmp/issue4197-s4a1-new/study/retained
S4A1_RETAINED=/tmp/issue4197-s4a1-new/study/retained python -S -B -m unittest -v test_verify test_reconcile test_restore
```

The archive preserves all original files of this review and the five inspected
historical public inputs, including the undecodable construction text. It does
not claim to restore that broken archive's original members. The restorer
requires a fresh destination, checks complete archive/member hashes and accepts
only bounded regular-file members. It does not import or execute archived code.
Publication files and temporary parents are trusted/quiescent; the restorer is
not an adversarial-filesystem sandbox. Temporary regression mutation copies
were removed by unittest; their exact transformations, original records and
first test output are retained, so the controls remain reproducible.

The default reproduction checks saved outputs only. `verify_readonly.py`
contains the consumed data-only collection command for inspection, not a native
allocation. It must not be mistaken for the missing historical live experiment.

## Integration decision and preservation

Existing #4197/#4202 first outcomes, public files and old comments remain
unchanged. Do not cite the older blanket independent-raw claim as a sufficient
adoption gate. The original source identity is now resolved; complete construction
publication and independently reconstructible native evidence are not.
This is a qualification correction under #4197, not a new fleet-wide research
objective. #4242, #2789, #3311 and the global ROADMAP remain separate.

No shared runtime, old evidence, or another worker's branch is modified.
Applicable remote CI and review are distinct from the local checks listed above;
see the PR for the current integration status.
