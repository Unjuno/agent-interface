# Retrospective GitHub publication note

Issue: #4080. Branch: `research/review-image-contract-delivery-20260922`.

This directory publishes an already completed conversation-local experiment. The original allocation was locally frozen and executed before Issue #4080 and this branch existed. Nothing here retroactively converts that local freeze into a GitHub preregistration.

Scientific result: `PASS_REVIEW_IMAGE_QUALIFICATION_SCOPED` for the exact 39-case synthetic presentation boundary recorded in `RESULT.md`. The candidate is read-only: it qualifies the already-returned image bytes and does not issue input, recapture, retry, replay, or alter the retained action outcome.

The full original 556-file research tree is retained losslessly as a 58,448-byte tar.xz capsule split across 12 Base64 text parts under `parts/`. `unpack.py` verifies each decoded part, the concatenated capsule SHA-256, safe member paths/types, and the frozen 556-file/833,770-byte inventory before extraction. The tar.xz container is a new publication encoding; the original ZIP container bytes are not claimed to be preserved. `PACK.json` binds both the historical ZIP hash and publication capsule hash. After extraction, the original `SHA256SUMS` verifies the member bytes.

Do not rerun the consumed `formal-01` allocation. Review and re-audit only.

Suggested read-only verification from this directory:

```sh
python -B unpack.py /tmp/review-image-contract-4080
cd /tmp/review-image-contract-4080/research/integration/review_image_contract_v1
sha256sum -c SHA256SUMS
python -B -m unittest -v test_contract
python -B audit.py formal-01 > /tmp/review-image-audit-4080.json
cmp AUDIT.json /tmp/review-image-audit-4080.json
python -B audit.py formal-01 controls > /tmp/review-image-controls-4080.json
cmp CONTROLS.json /tmp/review-image-controls-4080.json
```

The same-author raw-only auditor is a separate implementation/process, not independent human review. The result does not establish capture provenance, model viewing, task success, speed/token benefit, or production support.
