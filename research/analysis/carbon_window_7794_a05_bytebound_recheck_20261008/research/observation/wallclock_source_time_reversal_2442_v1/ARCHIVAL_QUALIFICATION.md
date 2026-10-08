# Branch recovery qualification — Issue #2442

This directory preserves all 13 paths added by remote branch `research/wallclock-source-time-reversal-2442-20260922-v1` at head `f7c8e4cdd946090c32fd7b5817f4a62352320fc0`, brought forward without content edits. The original 16-commit branch history is retained at `archive/recovered/wallclock-source-time-reversal-2442-20260922`.

## H/T/D/C/U

- **H:** retain the abandoned branch's source/protocol fragments and the exact allocation-01 stop evidence so later recovery does not erase the incomplete attempt or mistake it for a completed result.
- **T:** compared current main to the exact remote head; the branch contributed 13 previously absent paths. `FORMAL01_STOP.json` records allocation-01 at 10/34 complete cases, 66 captured frames, case 11 started without a RESULT receipt, no root END/STOP receipt, and unknown runner/Xvfb exits. No rerun occurred. For the preformal capsule, the freeze declares part hashes `80f490…` and `275166…`; recomputing SHA-256 over the exact non-newline base64 characters yielded `e9c458…` and `48e8e9…`. Concatenation decoded to SHA-256 `8320e3232800d935805308c1bf6d125333ce41e8538cba91c7549fa7905a8e1a`, not the declared `f8bbe9dc8ef8b16239eae010295f469fff804114754b005c46ed52dc6602a00e`; read-only tar listing reported corrupted input. GitHub's 32 associated Actions runs had no retrievable artifacts.
- **D:** preserve allocation-01 as `STOP_OUTER_TOOL_TIMEOUT_INCOMPLETE_DENOMINATOR`; preserve allocation-02 as `HOLD_PUBLICATION_INCOMPLETE`. This archive does not establish a scientific PASS/FAIL for either allocation and does not promote the Issue-reported material.
- **C:** a planned batching change and an Issue summary cannot replace the missing exact source capsule, terminal receipts, raw batches, and independent audit. Allocation-01 and allocation-02 remain distinct; no rows are pooled.
- **U:** allocation-02 raw/source/audit delivery is still absent, while the preformal capsule bytes fail their declared integrity check. Issue #2442 remains open for authenticated byte recovery; do not rerun allocation-01 or infer missing process exits.

This is preservation of the historical branch content plus an explicit integrity qualification, not a claim that the old package is executable or reproducible.
