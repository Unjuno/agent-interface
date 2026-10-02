# PR #6718 recipient-side publication correction

This additive packet audits exact PR head `df6ec1c350bc25e60d3c022bccd8b598134d6eaa`. The original T0 freeze, raw, audit and scientific disposition are not altered.

The PR tree declares two formal stdout logs in the original `SHA256SUMS`, but neither path exists as a Git tree entry. The producer checkout still has both local files and their local SHA-256 digests equal the original declarations. `LOCAL_ORIGINAL_LOGS.json` records this discrepancy and local Git blob IDs, but intentionally does not copy producer-only bytes into the correction. This correction therefore does not pretend to restore recipient availability of missing source-head bytes.

All other 22 declared entries verified against the exact source tree. An independently materialized raw JSON blob and auditor source from that tree were replayed without executing the candidate or original runner. The auditor reconstructed 24/24 rows, returned `PASS_METHOD_SCOPED`, and its JSON was byte-identical to the published audit blob. This supports raw/auditor reproducibility from the PR packet, but does not repair or explain the absent stdout logs.

Disposition: `LOCAL_RESULT_AUDITED`; raw/audit portion is recipient-reproducible; whole packet remains `HOLD_PUBLICATION_FIDELITY` because two declared bytes are absent. The original local scientific `PASS_METHOD_SCOPED` is unchanged. No formal experiment was rerun, no missing log was regenerated, and no missing bytes were silently substituted. A later correction may only claim the exact checks it independently verifies from a newly identified immutable Git tree.
