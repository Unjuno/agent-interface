# Approval-sequence assay — Issue #6405 T0

This package tests a finite **display and request-binding contract**, not
whether repeated prompts change human behavior. It uses five authored,
non-real approval requests and three render arms: static cards, source-bound
changed-field highlights, and a bounded batch that groups only eligible
nonconsequential effects.

## Frozen protocol and outcome

See [`FREEZE.md`](FREEZE.md) for H/T/D/C/U, exact hashes, gates, execution
boundary and single-use formal commands. Results and raw command receipts are
under [`results/formal-01/`](results/formal-01/). The candidate and raw-only
auditor are independent implementations; the auditor does not import the
candidate.

Construction checks:

```sh
python3 -m unittest -v test_construction test_audit_construction
```

The T0 can only pass the finite display/request contract. It cannot establish
habituation, attention, comprehension, approval discrimination, burden,
trusted-presentation authenticity, broker safety, or a beneficial batch policy.
T1 would require separate voluntary consent, privacy/accessibility review,
prospective randomized/counterbalanced vignettes, predeclared human outcomes,
and no consequential effects.
