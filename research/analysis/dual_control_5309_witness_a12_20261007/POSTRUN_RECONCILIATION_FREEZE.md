# A12 postrun reconciliation freeze — diagnostic only

Diagnostic allocation: `5309-A12-POSTRUN-POLICY-RECEIPT-RECONCILIATION-V1`.

This diagnostic was defined after the formal A12 output. It reads the immutable candidate input, oracle, choices, raw rows, and formal audit; it does not invoke or modify the formal candidate, environment, or auditor. It cannot change the frozen A12 verdict. Its purpose is to independently reconstruct the candidate's exact frozen policy choices (a check not performed by the original formal auditor), confirm equal information gain, independently rebind all raw transitions/receipts, and compare derived counts to the retained formal audit.

The diagnostic source and exact input bytes are bound by `POSTRUN_RECONCILIATION_SHA256SUMS.txt`. It runs once with:

```bash
node postrun_reconcile.mjs candidate-input.json oracle.json \
  out/candidate-choices.json out/candidate-raw.json out/audit.json \
  out/postrun_policy_audit.json
```

This is post-outcome verification, not another preregistered experiment and not a replacement audit. The A12 candidate/environment/auditor invocation counts remain 1/1/1.
