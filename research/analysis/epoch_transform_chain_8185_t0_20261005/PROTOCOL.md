# Issue #8185 T0 protocol

Allocation: `8185-TRANSFORM-GRAPH-T0-20261005-01`  
Base: `2c1c90c80389dc6aab6a950c7058528272979f2d`  
Host: macOS arm64; CPython 3.14.5. OrbStack's read-only image inventory returned an `operation not supported` error for a containerd content blob; no image pull, container start, or store repair was attempted. This CPU-only finite-model allocation therefore runs host-only under the Issue's no-GUI/no-model/no-input boundary; no container-isolation claim is made.

## H/T/D/C/U

**H.** A source/target-typed, epoch-bound affine transform chain with interval uncertainty can preserve correct target admission across valid composed display/capture/input changes, while reducing false UNKNOWN decisions by at least 20% relative to a capture-origin plus single last-known scale/offset baseline. It must reject every stale, incomplete, malformed, identity-swapped, or non-affine case.

**T.** Exhaustively evaluate a deterministic finite corpus. Public candidate input contains graph edges, validity epochs, bounded residuals, target identity, intended hit-region and forbidden regions. The independent oracle separately owns true affine transforms, target identity and hit regions. Compare (a) last-known single-scale/offset baseline, (b) typed graph composition with interval propagation, and (c) exact hidden-transform oracle. Cases cover stable layout, translation, uniform DPI update, mixed-monitor update, two-epoch composition, shared/common-mode uncertainty, independent-error control, stale epoch, missing/reversed/duplicate/unit-mismatched edge, changed input-DPI context, target swap, non-affine reflow, and uncertainty crossing a hit/forbidden boundary. The candidate receives only declared public graph/metadata; the oracle truth is stored separately and imported only by the auditor.

**D.** `PASS_METHOD_SCOPED` only if every candidate decision matches the independent oracle; all stale/unmodeled/malformed controls return UNKNOWN/REFUSE; false admissions are zero; and false UNKNOWN on valid composed-affine cases is at least 20% lower than baseline. Any wrong-target/forbidden admission, stale-chain acceptance, or corrupted composition accepted as valid is `FAIL_UNSOUND`. If baseline yields equal precision or graph does not meet the fixed 20% reduction, `FAIL_NO_INCREMENTAL_VALUE`. Unsupported/non-affine cases that cannot be reliably distinguished yield `HOLD_MODEL_MISMATCH`. No threshold changes or formal rerun follow the first result.

**C.** A fresh OS-provided mapping plus epoch invalidation may be sufficient; the graph may add complexity without reducing refusal. Target-semantic or application hit-testing error may dominate coordinate conversion.

**U.** Finite authored affine model only. No Windows API, DPI virtualization, native GUI, live hit test, user task, input, semantic effect, calibration distribution, performance, or safety evidence. Axis-aligned uncertainty bounds may be conservative; affine composition cannot represent layout reflow.

## Frozen execution

Construction checks may run before freeze. Formal commands, once each and in order: `python3 candidate.py`, then `python3 audit.py`. Candidate reads `candidate_input.json` and writes `candidate_output.json`; auditor independently reconstructs output against `oracle_truth.json`. Candidate and auditor invocation counts are 1 each, retries 0. Preserve all first outputs and hashes.
