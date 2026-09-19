# Postformal validation notes

The formal scientific result was not rerun after A2.

1. The first supporting postformal verifier used a newline in semantic-intent canonicalization that the frozen compiler does not use. It therefore returned eight identity mismatches. The formal rows were unchanged; the verifier was corrected to the exact frozen compiler definition and then returned `PASS_POSTFORMAL_VERIFY`. Both outputs are retained in the full archive.
2. The first corruption-control copy harness attempted to copy Chromium profile `SingletonSocket` runtime nodes and failed before mutation verdicts. The evidence-only copy harness then rejected four copied-evidence/source mutations 4/4.
3. The corruption-control outer tool invocation reported a supervision timeout after printing/writing all four completed verdicts. `corruption_controls.json` was present and complete; no formal case was involved or rerun.
