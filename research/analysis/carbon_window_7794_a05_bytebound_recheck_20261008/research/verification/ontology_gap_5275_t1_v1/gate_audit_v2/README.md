# Gate-integrity audit successor for #5457

## Result

`PASS_GATE_INTEGRITY_CORRECTION_SCOPED` on the one frozen retained-input
maintenance invocation. This is an additive correction to audit coverage, not
a scientific rerun and not a revision of the predecessor's frozen files.

The predecessor auditor accepted all five tested inconsistent metadata copies:
empty gates, missing gates, an undeclared gate, integer `1` instead of Boolean
`true`, and a coherently flipped gate/disposition. The successor rejected all
five. Inconsistent inputs yield `scientific_disposition: NOT_VALIDATED` rather
than copying an unvalidated submitted verdict into that field.

The original retained raw remains integrity-valid and independently reconstructs
the same `PASS_SCOPED_LEXICAL_BOUNDARY`: 13 rows, six supported cases, seven OOD
cases, combined false passes 0/7 and false abstentions 0/6. This does not prove
held-out generalization: all six supported evaluation strings are training
duplicates. The original report already discloses this limitation.

Nine test methods passed, including the exact gate-key/type checks, corruption
of rows/metrics/counts/nonfinite scores, and an explicitly synthetic coherent
FAIL control. That control changes one supported description to all-OOV words
and supplies matching outputs/counters: it is accepted as integrity-valid
`FAIL_LEXICAL_BOUNDARY`; an all-true gate/PASS relabeling is rejected. It is a
verifier test fixture, not an additional observed experiment row.

## Provenance and execution

- Original reviewed head: `bbf43bf7a569e9c79883756bef41cf7677e50239`
- Original raw SHA-256:
  `ce1219edc12ed3526c0be90043bfe3428db3d36e42c6337e6f532e18ae2c72d6`
- Additive freeze SHA-256:
  `c16fccbbd335516bc5952b2e58f5ec8402e5548853c63426f20dbf1167ab89ef`
- Retained receipt SHA-256:
  `183d1c1a9a6757f362d72ddcb01d7badd01ccaedfe48629f962a102dc0e0d99e`
- `launch-01/` retains the exact command, stdout, stderr, and exit 0
- `retained-01/` retains the complete mutation inputs/results, test transcript,
  separate CLI output/exit, source hashes, and environment/limit receipts
- CPython 3.12.14, Linux x86_64, existing execution workspace; no nested Docker
- Affinity restricted to one CPU; address-space cap 256 MiB per process, CPU
  time limit 15 seconds, outer wall timeout 30 seconds
- Wrapper elapsed 50.485 ms; parent/child reported peak RSS 15,828 KiB each
  (per-process observations, not an aggregate cgroup measurement)
- All nine frozen source/input hashes unchanged before and after
- Scientific candidate and runner executions: zero

Construction logs retain the TDD placeholder RED phase and the nine-method
GREEN result. Those placeholder failures are development checks; the actual
predecessor-auditor counterexamples are the separately retained controls.

## Recheck without rerunning science

From the repository root:

```sh
python3 -B research/verification/ontology_gap_5275_t1_v1/gate_audit_v2/audit_v2.py \
  research/verification/ontology_gap_5275_t1_v1/FORMAL-01.json
python3 -B -m unittest discover \
  -s research/verification/ontology_gap_5275_t1_v1/gate_audit_v2 -p 'test_*.py'
```

The consumed `verify_retained.py` invocation is not retried. A later reviewer
may rerun the read-only verifier/tests as maintenance checks, retaining their
own receipts. Neither command above executes candidate.py or run_t1.py.

## Limits

This fixes the scoped gate metadata/disposition trust defect and strengthens
typed row/metric comparison. It is not a universal hostile-JSON validator,
an authentication boundary, independent observation of original side effects,
or a runtime/model/task-quality improvement. The full repository is not present
in this sparse MCP-acquired workspace, so full-repository CI/build/tests are
not claimed. Publication, concurrent-author reconciliation, repository checks,
and merge remain separate parent-owned gates.
