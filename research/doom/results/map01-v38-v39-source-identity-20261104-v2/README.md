# v38/v39 source identity audit (2026-11-04)

The retained v38/v39 tempo analysis appeared to fail its source-hash audit on
Windows. The tracked Git blobs still matched the hashes in the retained
analysis and manifests; the working tree had CRLF line endings, so hashing the
checkout bytes directly produced different values. This was a cross-platform
audit defect, not evidence that the retained source had changed.

The read-only audit verifies the expected SHA-256 against each Git blob,
normalizes CRLF in the text checkout and compares it byte-for-byte with the
blob, then reconstructs the recorded metrics from the retained traces. All
four source blobs match, normalized checkout bytes match, and reconstructed
metrics match the saved analysis apart from transport-dependent raw hashes.
The ordinary posthoc auditor now passes on Windows after JSON/JSONL hashes are
computed over LF-normalized text.

Commands from the repository root:

```powershell
python research/doom/audit_map01_v38_v39_source_identity_20261104.py
python research/doom/audit_map01_v38_v39_control_tempo_posthoc_v1.py
```

This is a retained-data integrity and reproducibility result. It makes no new
game, model, input, allocation, task-effect, survival, latency-benefit, or
MAP01-completion claim.
