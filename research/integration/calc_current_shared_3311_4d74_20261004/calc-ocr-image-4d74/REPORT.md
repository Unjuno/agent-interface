# Standard OCR diagnostic for retained real Calc images

New WSLc image sha256:86edd8e13599b0e4e035b5865e4fee340740d349308a2a24a1304aa1cb41dde2 derives from the inspected existing f649ccab8aec3b94e451c6b0037e60fca72d7d7559381f8cd4aa98530b786c55 image. Build adds Debian Tesseract/English data and retains version/package lists in /opt. Dockerfile, first build log and resulting image identity retained. No host installation or old image modification.

One frozen no-GUI diagnostic used immutable post-input PNGs from G08 and G09. Six calls, three fixed cells each, resize4/border20, psm7, English digits whitelist; no parameter search or retry. Actual outputs were23,31,713 and20,31,620. Original source-image digests verified. Expected labels were scoring-only, not supplied to Tesseract. Host exit0 and independent returned-value/receipt reader found all six values exact. Raw version, complete OCR argv/stdout/stderr, derived cell crops and host swap warning retained.

This is retained-image evidence that a standard OCR option handles two rows rejected/unavailable under the custom binary-glyph method. It is not a new application effect, fresh live OCR integration, false-positive/reliability calibration, model/cost comparison, or regrading of G08's failure. The retained native allocations were not replayed. Next: use this pinned image and source configuration in a fresh GUI allocation with new values, preserving unknown versus readable mismatch, independent saved-byte scoring, and current native guard/release semantics. Full integrated comparison remains HOLD until that route is qualified.

GitHub publication remains pending previously observed content-creation rate limit. All prior failure/success/stop records remain unchanged; local evidence is not a PR or main adoption.
