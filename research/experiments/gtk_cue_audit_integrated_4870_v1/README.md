# Integrated raw-only audit — Issue #4870

This follow-up preserves the #4862 formal run, its source, output and historical context. It fixes the independent audit's ineffective weight mutation control by binding each weight row to SHA-256 over dtype, shape and contiguous bytes. The actual raw auditor independently recomputes the recorded ten probabilities from archived pixels/weights and tests 13 corrupted variants.

## Outcome

`results/integrated-audit.json` records PASS: original raw evidence is valid; all 13 corruption controls reject with the expected weight digest/dtype/shape reasons; formal result and NPZ SHA-256 hashes are unchanged. The one-shot formal result remains 10/10 shifted-color predictions over five seeds, with identical neutral text/layout. Audit used local offline CPU Docker only, with zero model calls, fitting, generated predictions, recaptures or retries.

## Integrity and limitations

- Runner SHA-256: `f42ce1c014a5c6a50dd13efdbed083b63fce284386665254559b280e9ff87e75`.
- Formal JSON SHA-256: `d6eca8b564bbd391f3cae2f34c7948af16e07b27745370b2ad06abb1de7e9a6a`.
- Raw NPZ SHA-256: `11109f60ebfbab32a28d1c18239d736052786807bcf5be318a9c3f60d004a935`; retained in the original local run directory, not committed here because GitHub MCP could not attach its binary blob.
- Scope is a tiny synthetic full-window cue, not localized GUI recognition, application transfer, safe authority or product readiness.
- The original #2599 report and prior audit STOP record remain unchanged.

See `FREEZE-passed.json` for source/input hashes and the governed command. Evidence PR #4872.