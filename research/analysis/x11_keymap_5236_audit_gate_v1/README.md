# Issue #5236: data-only auditor precedence successor

## Status and scope

This is ordinary deterministic maintenance verification of a pure-data classifier.
It is not a new X11 experiment, a Formal06 rerun, or formal evidence acceptance.
The retained Formal06 disposition remains `STOP_PROTOCOL_DEVIATION`; its saved
effects and frozen `FAIL_STALE_MAP_EFFECT` report remain diagnostic-only.
No predecessor source, source manifest, raw/wrapper, recorded audit, corruption
report, result disposition, or earlier allocation is changed by this directory.

The adapter gives **all reason strings already emitted by the pinned auditor**
STOP precedence. It preserves the complete old report in `legacy_result`.
It does not add missing validation, verify all required evidence, establish
preregistration, authenticate bytes, or make malformed input safe. The predecessor
has input-shape/type blind spots and can raise on malformed nested data; those
exceptions and blind spots are unchanged. Callers must not interpret this narrow
adapter as a total or comprehensive evidence validator.

## Dependency identity

Read-only intake main: `9fc98feb617c26fe1baa7ecc4decd43b69df8601`.

The only repository code dependency is
`research/x11_midprogram_keymap_5236_formal06_20261001/audit.py`:

- Git blob: `e29c897961668d4607b2d2b5608c7ab17554b155`
- SHA-256: `028eb71821cdcf162f1cc0efed722351bd310c7261564c2ba904ae22f721508a`
- Length: 12,609 bytes

The source identity is verified before each recorded maintenance-test batch.
This pin is a dependency check, not authentication of experimental evidence.
`gate.py` imports and calls only the dependency's pure `audit(raw, wrapper)`
function. It never calls the dependency's `main`, runner, or historical tests.
It does not perform runtime pin enforcement itself; maintenance use is qualified
by this exact dependency identity, which must be rechecked if the source changes.

The fixtures are independently constructed dictionaries. Command strings,
paths, namespace IDs, timing values and manifest entries are synthetic inert
data. They are never executed or represented as real process/source receipts.
The fixture manifest exercises only the existing equality check; it is not
evidence of a complete source manifest or a valid formal launch.

## Exact decision contract

| Synthetic data condition | Successor decision |
| --- | --- |
| All exact effects; no legacy reasons | `NO_STALE_EFFECT_OBSERVED` |
| Both remaps validly refuse at op 6; no legacy reasons | `PASS_MIDPROGRAM_REMAP_FAIL_CLOSED` |
| Present wrong effect in either completed remap; no legacy reasons | `FAIL_STALE_MAP_EFFECT` |
| Existing evidence reason, including with a wrong effect elsewhere | `STOP_PROVENANCE_OR_RUNNER` |
| Completed remap missing its effect | `STOP_PROVENANCE_OR_RUNNER` |
| Invalid control effect/status | `STOP_PROVENANCE_OR_RUNNER` |
| One exact remap and one valid refusal | `STOP_PROVENANCE_OR_RUNNER` |

`omitted_row`, `swapped_direction`, `wrong_expected_bytes`,
`missing_actor_receipt`, and `missing_post_save_wait` must each yield exact STOP,
both on an exact-effect seed and on a wrong-effect seed. The tests assert the
expected existing reason, effective mutation, and unchanged original data.

A changed but otherwise valid saved outcome remains a semantic FAIL. No
independent trusted byte binding is introduced, so this does not claim to detect
tampering. The five evidence controls and semantic wrong-effect controls are
not combined into the predecessor's ambiguous "all non-clean means rejected"
metric. The complete predecessor report is retained even when its decision
differs from the successor decision.

## Maintenance-test evidence

`evidence/initial_red_test.py.txt`, `initial_red.log`, and `initial_red.json`
retain the pre-implementation regression. One test method exercised five
subcases against the predecessor: three assertion failures demonstrated the
priority bug, with zero errors. Omitted-row and swapped-direction already STOP.
The expected failures were not retries of a formal allocation.

`evidence/initial_green.log` and `initial_green.json` record 17 new test methods
passing, zero failures/errors, including ten exact-verdict evidence-mutation
subcases (five on each seed), cross-row evidence faults, wrapper/source reasons,
control failure, missing effect, invalid release, exact/refusal/mixed/wrong
outcomes, mutation effectiveness, and seed immutability.

Independent static review requested full reason-list equality instead of only
membership. `evidence/review_strengthened_green.log` and its JSON metadata retain
the fresh 17/17 pass after that test-only strengthening. The swapped-direction
case expects exactly the two ordered row-ID reasons; the other four mutations
each expect exactly their one documented reason. Earlier logs remain unchanged.

Each batch was a single Python 3.12.14 process with one-core CPU affinity,
512 MiB `RLIMIT_AS`, 60-second `RLIMIT_CPU`, and a 60-second wall alarm.
Only this directory's selected new tests and the pinned pure function ran.
No old CLI/suite, runner, child process, Xvfb, GUI/thread fault, provider, model,
network experiment, or retained Formal06 raw re-audit was performed.
The repository-wide suite and CI were not run and are not claimed to pass.

Local staging initially added one extra newline when materializing the dependency;
the Git blob check caught it before any import or test. Removing that transfer-only
newline produced the exact pinned blob above. No remote/frozen source was edited.

To reproduce the bounded test selection in an authorized maintenance process:
set one-core affinity, `RLIMIT_AS=536870912`, `RLIMIT_CPU=60` and wall alarm=60;
verify the dependency hash; load only
`research.analysis.x11_keymap_5236_audit_gate_v1.test_gate` with `unittest` and
run its suite in that same process. Do not discover the predecessor's test suite
or execute the retained red-test text as a passing test.

Independent review and publication are separate gates. The initial ownership
check found no assignee on #5236 and no overlapping successor among 68 open PRs;
historical #5244/#5250 remain separate. Recheck current ownership immediately
before any remote publication. This directory does not close #5236.
