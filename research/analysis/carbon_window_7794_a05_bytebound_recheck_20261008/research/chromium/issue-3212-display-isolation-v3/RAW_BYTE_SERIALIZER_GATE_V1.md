# #3430 raw-byte serializer gate v1

Decision: PASS_RAW_BYTE_SERIALIZER_CONSTRUCTION_SCOPED

This is a construction gate only. It is not a fresh GUI allocation and does not repair or relabel #3419 allocation 2.

## H/T/D/C/U

- H: The corrected v3 experiment can distinguish and bind exact LF JSONL bytes from a literal backslash-n representation before formal collection.
- T: Fresh Python 3.12 Alpine container; construct the same two logical JSONL records with actual LF bytes and literal backslash-n bytes; compute both SHA-256 values and require them to differ.
- D: Retain both byte encodings and hashes in the gate output. The formal v3 allocation must hash the exact attached raw file bytes, not a reconstructed display string.
- C: PASS requires distinct encodings and distinct hashes; any formal allocation still requires independent recomputation over the attached file.
- U: No Chromium/X11 process, input, application effect or GUI reliability claim.

## Obstac result

OBSTAC_RAW_BYTE_SERIALIZER PASS lf_sha=39025f7d466b939459759da461466bb4ed2911646a2639c353b4b2f078db065e escaped_sha=6200ade46d0d00e993bd3a0e4fd3bf1ad1b43b931c643d723b2ef458911831f9 distinct=True

## Formal next gate

Run a new #3430 GUI allocation only after writing raw bytes to an explicit file, hashing that file, publishing the exact bytes, and independently recomputing the same hash in a separate container. Allocation 2 remains immutable HOLD_RAW_BYTE_MANIFEST_MISMATCH.
