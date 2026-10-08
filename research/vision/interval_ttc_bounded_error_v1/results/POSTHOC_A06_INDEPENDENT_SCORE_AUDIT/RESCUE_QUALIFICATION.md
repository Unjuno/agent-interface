# Rescue qualification — Issue #8157 A06

- Source PR #8262; branch `research/8157-posthoc-score-a06-20261007`, head `a816126d8278b303faedb5d4d06516fe20eee120`, historical base `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`.
- The eight source-branch files in this A06 package are byte-identical to their source blobs. The retained root-relative `SHA256SUMS_A06.txt` verifies 7/7 referenced artifacts.
- The record is a one-shot audit-only STOP: four construction preflight tests had passed, but the sole scorer invocation exited before parsing JSONL because the A06 three-key artifact map did not equal A04's four-key map (which includes `first_audit`). No score was produced; A02 remains `FAIL_METHOD`/unscorable and predecessor dispositions are unchanged.
- No candidate, generator, earlier auditor, container, model, GUI, or input was run during rescue. The STOP and invocation were not altered or retried. This is custody of a harness STOP, not a TTC-method result.
