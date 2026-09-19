# Successor #1968 result

## H/T/D/C/U

- **H**: canonical serialized multi-resolution packages can be smaller than FULL while preserving exact authoritative recovery and positional/contextual disambiguation of visually identical labels.
- **T**: deterministic 64x40 fixture with two identical label regions (`label_left`, `label_right`) plus toolbar, dialog, and tiny status. Compare canonical JSON serialization of FULL versus low-resolution plus lossless positional patches across seven changed cases.
- **D**: 14 rows, canonical serialized byte lengths and SHA-256 hashes, exact reconstruction flags, manifest SHA-256, and explicit duplicate-label cases.
- **C**: PASS only if both arms reconstruct all rows exactly, reduced serialized size is smaller than FULL on a nontrivial case, and left/right identical labels remain separately addressable.
- **Competing explanations**: the reduction may depend on the deterministic base recipe, truth-selected patches, and synthetic compression/layout; no automatic attention discovery is exercised.
- **U**: model usability, token/latency benefit, GUI correctness, and cross-domain transfer remain unknown.

## Formal result

```text
FULL                  exact 7/7, serialized bytes 5182
GLOBAL_LOW_PLUS_PATCHES exact 7/7, serialized bytes 445, 581, 606, 609, 724, 771, 1550
rows                  14
manifest SHA-256      63ae3c2b57cb969352d8921e67ea4b85ad77f6e9a24b0d94207d88c7ecc90f79
```

The two visually identical labels are independently changed and jointly changed; all cases recover exactly using positional/contextual patch metadata.

**Scoped outcome: PASS_SERIALIZED_MULTI_RESOLUTION_DUPLICATE_LABEL_SCOPED.**

This is a deterministic analytical fixture only. It does not establish model, token, latency, GUI, or cross-domain benefit.

