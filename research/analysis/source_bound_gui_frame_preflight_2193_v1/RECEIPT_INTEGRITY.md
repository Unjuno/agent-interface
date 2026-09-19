# Receipt integrity negative tests

The canonical Docker fixture was not modified. The verifier was run against three in-memory cases:

- normal receipts: `(True, pass)`
- one tampered `target_present`: `(False, receipt_label_mismatch)`
- one omitted receipt: `(False, receipt_count_mismatch)`

Both failure modes were detected and asserted. This establishes a fail-closed integrity gate for the controlled fixture; it does not establish trust in an uncontrolled GUI source.
