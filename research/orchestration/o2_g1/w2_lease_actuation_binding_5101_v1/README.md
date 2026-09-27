# W2 lease-to-actuation binding — construction package

Issue: [#5116](https://github.com/Unjuno/agent-interface/issues/5116), successor to #5101. This package is additive and does not modify the original W2 fixture or its reports.

## Scope / revised interpretation

The unchanged eight-case W2 runner is the compatibility baseline, not eight positive lease-binding examples. Four cases contain input edges under a lease whose `LEASE_OPEN.lineage.actuation_id` is absent: `release-before-terminal` (A4), `overlapping-key-holds` (A5), `missing-and-out-of-order-edge` (A6), and `held-input-no-effect` (A8). Under an exact-binding rule these four legacy rows must be reported HOLD; they cannot also retain authorized status. The original fixture remains byte-for-byte unchanged. Four separately versioned in-memory positive copies add the matching A4/A5/A6/A8 identifier; each also receives independent foreign-ID and missing-ID controls.

## Hypothesis and decision gate

H: A lease-open record with no exact actuation binding must not authorize edges bearing that actuation ID; only an explicit one-to-one match is admitted. Reused lease IDs are ambiguous and HOLD.

T: Run the deterministic host construction tests against the exact frozen eight-case fixture. Candidate and raw-only oracle are separate modules. For each of the four binding-required cases, test a matched positive, a `FOREIGN-ACTUATION` mutation, and an absent binding. Also test reused lease ID and edges without a lease-open.

D: Construction PASS requires frozen-fixture SHA-256 match, unchanged eight baseline cases, candidate/oracle agreement, 4/4 matched positives, 4/4 foreign mutations rejected, 4/4 missing bindings held, and both structural controls held. This does not pass the Docker formal/audit gate in #5116. Any candidate/oracle disagreement is a construction FAIL; source drift is STOP.

C: Synthetic traces only; one field changes in each positive/negative pair. This tests actuation binding only, not lease time windows, owner/session matching, input occupancy, clock conversion, GUI behavior, or runtime admission.

U: Construction evidence only. It establishes no live authority, product safety, model or GUI correctness. The distinct pinned Docker runner and independent raw artifact audit remain unperformed because the shared desktop-linux container ownership is currently unresolved.

## Reproduction

The committed fixture is an exact-byte copy of the frozen source fixture at `fixtures/trace-cases.json` (Git blob `0a49a00567c25766495cd332be50f6c2946781f7`; SHA-256 `6a693f06b1b4be15a8da35ec3aaf806d7fb3601091c8ef638c516069d1b4e95f`). Run:

```powershell
$env:W2_TRACE_FIXTURE = "fixtures/trace-cases.json"
python -m unittest -v test_binding.py
```

The test writes no files. The independent auditor reads only event rows and never imports the candidate implementation.
