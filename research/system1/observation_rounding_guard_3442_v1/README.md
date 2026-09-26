# Observation-rounding guard — Issue4045

Research-only result: **PASS_ROUNDING_PREIMAGE_BOUNDARY_SCOPED**. Per158 directed sources, the existing post-conversion binary32 predicate permits11 pre-conversion-invalid values; promoting rounded values to binary64 permits7; a complete-rounding-cell guard permits0 but refuses15 valid boundary values. Two actual conversion workers agree. This does not refute the old predicate's explicitly binary32 contract, improve model quality, or promote production behavior.

- REPORT.md: result, retained failure, limitations and adoption decision.
- certify.py: directly reviewable interval candidate (no input authority).
- FREEZE.json: public preformal15-file hash commitment.
- PACKAGE.json and capsule parts: complete current source/input/formal/audit/receipt/proof evidence, including unchanged predecessor candidate/report/proof but NOT the full previous chat ZIP.
- unpack.py: bounded data-only reconstruction into a NEW output directory, no experiment execution.

From this directory:

```sh
python -B -S unpack.py /tmp/rounding4045-review
cd /tmp/rounding4045-review
python -B -S -m unittest test_contract -v
python -B -S audit.py . > /tmp/rounding4045-reaudit.json
cmp AUDIT.json /tmp/rounding4045-reaudit.json
```

The audit requires only Python standard library. Do not rerun the consumed formal allocation or overwrite its output. No Python -O. Full proof with variable/units table is inside the reconstructed PROOF.md. Exact fixture/runner can be examined without importing Torch or running a worker.

The source hash commitment was public before formal execution; most full source bytes were delivered afterward. This is not a retrospective GitHub preregistration. The earlier model-quality FAIL and its binary32 proof remain unchanged. No shared runtime/workflow/root-document or other worker branch is modified.
