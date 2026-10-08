# Delivery qualification v2 — keep one runtime repair lane

The earlier PR #6866 was published before this worker's intake. A non-author
overlap check on #57 and PR #6887 identified it after my first publication. My
Issue-only intake failed to find that active PR; this was a search coverage
error, not absence of an existing owner. Exact Git readback verifies that #6866
head `abd318643112150d073a242926494145c6461e33` and this worker's original
head `8b7ba212e123f71591166ee056e7d043e91f93f8` have identical contract blobs:
`c6b16b9b6d43c837b354b20dc0ae452599d02043`, SHA256
`e0320ae7853cdadfd5820577cc7e166a60210b822afc8b6ca910eb64fd1b5965`.

PR #6866 owns runtime delivery. This successor PR #6887 adds evidence only:
production `runtime/core_v1/contract.py` is restored to its review-base bytes,
and the added runtime regression file is removed from the runtime test tree.
The original source/test bytes are retained as explicit source witnesses.
No file in another worker's branch is changed. The original head remains in
this branch's history; there is no force push or rewrite of source/raw history.

The original content proposal `9f3832ba...` is held/superseded. Its committee
acceptance and any technical reviews remain evidence, not votes for this changed
delivery. A fresh evidence-only content proposal is required before approval.

## Preserved independent evidence

All original 20 package files, including README, PUBLIC_MANIFEST, original
auditor, before/fixed raw, fixtures, logs and receipts, remain byte-identical.
Their interpretation is historical execution at the original head, not a PASS
for the restored production source in this successor tree. In particular the
old manifest's two runtime paths bind the original head; they are NOT hashes of
the production paths in the evidence-only successor.

The supplemental manifest provides exact aliases:

- original runtime contract -> `source-witness/contract.fixed.py`;
- original runtime test -> `source-witness/test_admission_context.py`;
- pinned baseline contract -> `source-witness/contract.before.py`.

The witnesses are data for provenance and read-only auditing; they are not
installed runtime modules or a second implementation to adopt. The fixed witness
matches the exact source used in #6866 and in this worker's retained 44-row run.
The independently executed 68-method core/121-method CLI checks, baseline failures,
44-row before/fixed observations and nine corruption controls remain attributable
to this worker. They do not replace or recover #6866's disclosed lost original
log bytes. They corroborate the identical scalar guard from a separate execution
and preserve their own original logs privately.

`audit_replication_v2.py` is an additive raw-only audit. It preserves the original
oracle and uses byte-preserved source witnesses for both identity gates. The
fresh receipt `audit-replication-v2.json` reports 44/44 reconciliation at both
stages, baseline 30 decision gaps/four exceptions, repaired zero, and 9/9 rejected
corruption controls. No producer matrix, runtime suite, formal allocation,
native backend, input, model, GPU or container is rerun for this conversion.

```sh
python runtime/results/admission-context-01a0ff2d/audit_replication_v2.py /fresh/replication-audit.json
```

This delivery supports the existing #57 / #6866 guarded-admission result. It is
independent engineering replication, not a novel scientific hypothesis or proof
of physical currentness, execution/release, task benefit, timing, thread safety,
or foreign-platform behavior. Main still requires non-author approval of the
new evidence-only proposal, current-base combination verification and conditional
application. The common fleet deadline was not reset; no resource/apply lock exists.
