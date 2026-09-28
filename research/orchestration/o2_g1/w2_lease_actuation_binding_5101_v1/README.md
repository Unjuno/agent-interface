# W2 lease-to-actuation binding — construction package

Issue: [#5116](https://github.com/Unjuno/agent-interface/issues/5116), successor to #5101. This package is additive and does not modify the original W2 fixture or its reports.

## Scope / revised interpretation

The unchanged eight-case W2 runner is the compatibility baseline, not eight positive lease-binding examples. Four cases contain input edges under a lease whose `LEASE_OPEN.lineage.actuation_id` is absent: `release-before-terminal` (A4), `overlapping-key-holds` (A5), `missing-and-out-of-order-edge` (A6), and `held-input-no-effect` (A8). Under an exact-binding rule these four legacy rows must be reported HOLD; they cannot also retain authorized status. The original fixture remains byte-for-byte unchanged. Four separately versioned in-memory positive copies add the matching A4/A5/A6/A8 identifier; each also receives independent foreign-ID and missing-ID controls.

## Hypothesis and decision gate

H: A lease-open record with no exact actuation binding must not authorize edges bearing that actuation ID; only an explicit one-to-one match is admitted. Reused lease IDs are ambiguous and HOLD.

T: Run the deterministic host construction tests against the exact frozen eight-case fixture. Candidate and raw-only oracle are separate modules. For each of the four binding-required cases, test a matched positive, a `FOREIGN-ACTUATION` mutation, and an absent binding. Also test reused lease ID and edges without a lease-open.

D: Construction v1 PASS requires frozen-fixture SHA-256 match, unchanged eight baseline cases, candidate/oracle agreement, 4/4 matched positives, 4/4 foreign mutations rejected, 4/4 missing bindings held, and structural controls held. See the append-only v2 extension below for the scalar/multi-actuation rule. Neither host stage passes the Docker formal/audit gate in #5116.

C: Synthetic traces only; one field changes in each positive/negative pair. This tests actuation binding only, not lease time windows, owner/session matching, input occupancy, clock conversion, GUI behavior, or runtime admission.

U: Construction evidence only. It establishes no live authority, product safety, model or GUI correctness. The distinct pinned Docker runner and independent raw artifact audit remain unperformed because the shared desktop-linux container ownership is currently unresolved.

## Reproduction

The committed fixture is an exact-byte copy of the frozen source fixture at `fixtures/trace-cases.json` (Git blob `0a49a00567c25766495cd332be50f6c2946781f7`; SHA-256 `6a693f06b1b4be15a8da35ec3aaf806d7fb3601091c8ef638c516069d1b4e95f`). Run:

```powershell
$env:W2_TRACE_FIXTURE = "fixtures/trace-cases.json"
python -m unittest -v test_binding.py test_binding_v2.py
```

The tests write no files. The independent auditor reads only event rows and never imports the candidate implementation. The original v1 test/freeze/result remain unchanged; v2 is a separate six-test extension.

## Append-only scalar/multi-actuation resolution

The frozen schema provides a scalar `actuation_id` on lineage and does not define a bounded `actuation_ids` set or lease-to-actuation cardinality. The conservative v2 experiment rule binds a lease-open to exactly one actuation; another actuation under the same lease is rejected unless a future version explicitly specifies a bounded set. This is a scoped test rule, not a claim that the broader protocol contract has formally selected this cardinality. See `FREEZE_v2.json` and `RESULT_v2.json`; v1 records above are preserved verbatim.

## Frozen full-CLI counterexample

[`host_cli/REPORT.md`](host_cli/REPORT.md) records a separate Windows host-CPU execution of the exact frozen W2 verifier and raw auditor CLIs against baseline and a one-field foreign lease-open actuation mutation. Both full CLIs accept the mutant; the target remains authorized with 298/302 ns bounds and raw audit errors are empty. This is stronger host reproduction than the prior function-only probe, but remains explicitly non-container/non-formal. Raw outputs and hashes are retained under `host_cli/`.

## Append-only v3 candidate/auditor CLI construction

`binding_gate_cli.py` creates versioned effective traces and a candidate report without changing the frozen fixture. `audit_binding_gate.py` is launched separately and reconstructs binding decisions from event rows without importing candidate code. Its negative test tampers with a candidate disposition and confirms that the raw-only auditor exits nonzero.

The v3 freeze and result are `FREEZE_v3.json` and `RESULT_v3.json`; `CLI_REPORT_v3.md` summarizes the H/T/D/C/U and the four raw CLI runs. On Python 3.12.10, the retained v1, v2, and v3 suites pass 15/15. Baseline, four matched bindings, one foreign binding, and one missing binding each audit all eight cases and reconstruct 14 decision rows: 11 input-edge rows plus three `NO_INPUT_EDGE` rows. The 12 run outputs and their SHA-256 digests are retained under `cli_v3/`.

Reproduce the combined suite from this directory:

```powershell
$env:W2_TRACE_FIXTURE = "fixtures/trace-cases.json"
python -m unittest -v test_binding.py test_binding_v2.py test_binding_gate_cli.py
```

This remains host-CPU construction evidence only. It does not satisfy the separately gated Docker/formal run, and it makes no live-input, GUI, runtime-authority, or broader protocol claim.
