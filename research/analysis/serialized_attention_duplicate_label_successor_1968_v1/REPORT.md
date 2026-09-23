# Serialized multi-resolution attention successor (#1968)

Decision: PASS_SERIALIZED_ATTENTION_DUPLICATE_LABEL_SCOPED

H/T/D:
- Deterministic 32x24 synthetic GUI fixture.
- Two visually identical labels use distinct positional/contextual identities: left=Save, right=Cancel.
- Canonical JSON serialization, same encoder for FULL and reduced package.
- Cases: unchanged, changed_left, changed_right.
- Exact authoritative reconstruction: 3/3.
- Reduced serialized bytes: 351/1624, 354/1624, 355/1624.
- Negative control omitting the changed crop fails exact recovery as expected.
- formal=1, audit=1, reruns=0, tuning=0.

C/U:
This is fixture-truth-derived candidate selection, not automatic attention discovery. It proves only exact serialized recovery and duplicate-label disambiguation on this fixture. No model usability, GUI correctness, token/latency, cross-domain, or runtime claim. Stop after this result; a broader successor must test non-truth-derived region proposals and additional encoders.

Additive path only: research/analysis/serialized_attention_duplicate_label_successor_1968_v1/**
