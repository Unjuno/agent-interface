# Retrospective delivery: referenced-image retention 6c29

This directory publishes the already executed 24-case first rung recorded in Issue #4064. It is not GitHub preregistration and it does not rerun science. The historical STOP_GITHUB_WRITE_CAPABILITY_UNAVAILABLE remains preserved inside the exact reconstructed patch.

Scientific disposition: PASS_REFERENCED_IMAGE_RETENTION_SCOPED. Reference-only storage recovered the original image in 2/8 and returned the wrong image in 2/8; digest-only recovered 2/6 committed cases while rejecting wrong or missing references; retain-bytes recovered 6/6 committed cases and refused the two already-missing sources before cursor advance. Formal reruns: 0.

The exact original additive git diff --binary is split under full_patch/. Reconstruct with `python -B reconstruct_patch.py /tmp/image-retention-6c29.patch`; the script verifies every part plus the final patch SHA-256 before writing. Applying that patch to a fresh tree restores the complete 66-file research namespace, including lossless Base64 evidence parts. Do not run the consumed formal runner; use the restored audit/unpack instructions only.

This delivery resolves only the first-rung publication gap. Issue #4064's later 36-case PASS_IMAGE_DEPENDENCY_BUDGET_SCOPED currently has a separate HOLD_PUBLICATION_SOURCE_RAW_UNAVAILABLE_IN_CURRENT_SESSION; this directory does not invent or regenerate those missing second-rung raw/source bytes.

No production runtime, ACK/model-consumption, GUI, performance, product or global-roadmap claim.
