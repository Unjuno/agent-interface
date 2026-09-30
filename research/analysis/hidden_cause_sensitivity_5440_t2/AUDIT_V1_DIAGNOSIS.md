# Preserved v1 audit failure diagnosis

The one-shot candidate completed successfully and wrote `output/raw.json`.
The frozen v1 independent auditor ran once, emitted `FAIL`, and exited 1. Its
raw audit result is retained unchanged at `output/audit.json`; do not overwrite
it, and do not rerun the candidate.

Inspection isolates two auditor-side construction mistakes:

1. `audit.py` hard-coded the pre-freeze base SHA
   `bde4e1d8a3bedfa16aefbb993a816fb3b0f65c92`; the last pre-run ref check and
   candidate raw correctly used frozen main
   `a2469a821f4d27d2ec9a1d5d63ed8b81e57f81c3`.
2. For `wrong_scope_digest`, `audit.py` expected the output's
   `declared_family_sha256` field to be zeroed. The candidate correctly reports
   the canonical declared graph digest in that field; only the synthetic
   attestation's *presented* scope digest is wrong, and the gate rejects it.

This is an implementation failure of audit v1, not evidence of candidate
failure or a scientific result. A new raw-only audit v2 has a separately
frozen source and may inspect this already-produced raw once. No T2 candidate
or raw generation is repeated. The original v1 failure remains part of the
record even if v2 validates the raw.
