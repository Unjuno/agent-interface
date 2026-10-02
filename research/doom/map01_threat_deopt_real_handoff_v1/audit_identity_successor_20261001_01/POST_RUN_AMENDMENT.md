# Post-run provenance amendment (append-only)

This amendment was written after the one-shot candidate and new-auditor invocations. No frozen source or result was modified.

The frozen PLAN.md and the docstring in `legacy_audit.py` incorrectly represented the local file as an exact copy of the SHA-bound original. Its observed SHA-256 is `14a5f6a8c7a5ba208aa15d24b983735486e29f8519a817cf640399b5314e950d`, not the frozen original `7ab3d8895c9e8d7c80cf4ff463bac0623fb39247f8aa0d65f34941a1f8c48a40`. This discrepancy invalidates the planned old-auditor comparison and the old-auditor wording in the preregistration. Preserve the contradiction as provenance evidence; do not silently replace the file or reinterpret its output.

Accordingly, `legacy_audit_result.json` and the legacy portion of `mutation_results.json` are outputs of a non-identical local transcription only. They are not results from the original frozen auditor. The new auditor's synthetic six-row pass and mutation unit tests are local contract-construction evidence only; because the comparator provenance failed, the allocation-level decision is STOP and no formal #626 work may rely on this bundle.

The source-base annotation in FREEZE.json records the observed preregistration base. Main later advanced to `45a1e0de5d8ccb45959b6e59a71fc5e8ec93cc3f`; publication was prepared from that later base. No source dependency on intervening commits was intentionally consumed, and the additive target directory was absent at the collision check.
