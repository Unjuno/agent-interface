# Construction-only history

No formal experiment has run in this directory yet.

| Branch commit | Check | Outcome | Interpretation |
|---|---|---:|---|
| `493b8369ec88a074ad0da14d55c8c57aec7f3118` | Runner construction smoke | 6/7 | `label_vocab` failed because an eight-row random sample was assumed to contain every class. No training, optimizer update, held-out data, or formal measurement ran. |
| `1180051522f2b997471933ed8dfb524ae00885c5` | Runner construction after fixed-fixture correction | 7/7 | All four labels and output shape are tested with deterministic examples; paired-state and fail-closed gate checks pass. |
| `a682a10116c9c7bbeadcbb38b1230e59c23c90c9` | Independent auditor self-test | 4/4 | Pure label-rule controls pass; then-current source hash pinning was added in the subsequent frozen audit commit. |

The first failure is retained as a construction-validation defect, not a scientific FAIL. The corrected runner and auditor are frozen by hashes in [PREREG.md](PREREG.md). Construction checks are not pooled with the one formal allocation.
