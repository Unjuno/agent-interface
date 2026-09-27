# PR #4645 review follow-up

The review correctly distinguished positive contrary evidence from missing evidence. The original v1 audit/result remain byte-for-byte preserved. The additive v2 audit reports the retained, same-run `Map State: IsUnMapped` as `CONTRADICTED_WINDOW_VISIBILITY` (exit 1), not STOP; missing/ambiguous map-state evidence remains STOP. Live-versus-disk evidence remains as previously observed and does not validate a visible VCL implementation window.

The v2 audit also reads a directly retained `baseline.xlsx` when available, or falls back to the published `baseline.xlsx.b64` file in the checkout without writing a decoded artifact. A unit test exercised this base64-only read path. Six tests passed in the pinned LibreOffice container; the full posthoc v2 classification used the local retained workbook file and reports its SHA-256.

Posthoc v2 audit JSON SHA-256: `f6987b735cba78d71fef5efe0c7922c83d593640379d61d2f50a7a8829b77e9d`. Audit source SHA-256: `4ed3ac03910e653a9855c34f966c0e732db68ca3c831cdc6dc7d46b0ff572f61`; test source SHA-256: `eee88b11040eeee75dabbb74da7333d7add20dfbd5d5987fd1e9d2c8b8853ede`. This is reclassification of immutable evidence, not a rerun.
