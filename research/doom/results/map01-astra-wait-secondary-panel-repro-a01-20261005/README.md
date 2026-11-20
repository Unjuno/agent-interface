# Cross-environment reproduction check A01

## H / T / D / C / U

- **H:** Test whether the retained A01 source/frame audit reproduces the historical 60 decoded RGB frame digests in the current macOS ARM64 environment.
- **T:** Read only the video blob pinned by the immutable A01 freeze and compare all decoded timestamps, dimensions, and RGB SHA-256 values against its retained `raw.json`. Do not rerun the original decoder/candidate and do not modify the original package.
- **D:** `PASS_REPRODUCED` only if all 60 complete rows match. Any mismatch is `STOP_DECODER_REPRODUCIBILITY`; report counts and examples without substituting new digests into the old record.
- **C:** The original freeze names PyAV 18.1.0 but does not identify the host, FFmpeg libraries/build, decoder flags, or a container image. Matching PyAV versions do not guarantee matching decoded RGB bytes.
- **U:** This is a cross-environment artifact reproducibility check only. It does not revise the historical manual review, independently validate the corrected visual interpretation, establish controller-frame identity, or rerun any game/model/input allocation.

## Current run

- Historical source commit: `81a59aed13492ba1d52ea80e03d48c3d8de7b2c5`
- Historical video blob: `983e2f43e878b56d0d05cd4d7db5125a55566cc8`
- Historical A01 package commit: `619a315adfcff281c452af6b44dfba4dda4de05b`
- Environment: macOS 27.0.1 arm64, CPython 3.12.10, PyAV 18.1.0, Pillow 11.3.0; bundled libavutil 60.26.102, libavcodec 62.28.102, libavformat 62.12.102, libswscale 9.5.102.
- Result: `STOP_DECODER_REPRODUCIBILITY`. Source blob identity and video SHA-256 match the freeze; 60 frames decode at the expected timestamps/dimensions, but **0/60 RGB digests match**. The original `audit.py` exits 1 at `assert rows == RAW["frames"]`, starting at frame 223. No replacement raw output was written.
- The original 18-entry SHA256SUMS manifest verifies when CRLF line endings are normalized for the local `sha256sum` utility. Original files and the historical `audit-result.json` remain unchanged.

Reproduce with `python audit_repro.py` from this directory, with PyAV 18.1.0 installed and the referenced Git objects available. Exit 0 means the frozen rows match; exit 1 preserves the reproducibility STOP. The script is read-only.
