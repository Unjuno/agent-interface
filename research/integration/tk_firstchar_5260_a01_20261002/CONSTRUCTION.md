# Construction record — Tk first-character A01

This directory contains only pre-formal runner/auditor construction checks.
The 96-trial allocation in `PREREG.md` was **not run** because the linked
Issues do not authorize it. Construction attempts are never counted as formal
replicates.

The pinned-base OrbStack image is built from `tk-xkb-refresh-4664:20260927-01`
(base digest `sha256:4c62a3d908f6bffdbff88b28eeff305bed40f5d6fcee029b7c0a3fa2ea5a86d6`)
and adds Openbox, XWD, ImageMagick, Tesseract, and fonts. Final local image digest
for smoke-03: `sha256:29b4131f68497276cdebc816b6e3a50354a459064edbff57538340fd3ab54118`.

| Attempt | Candidate | Independent audit | First disposition |
|---|---:|---:|---|
| smoke-01 | exit 0 | exit 2 | `FAIL_AUDIT`: baseline/path metadata assumptions and OCR tool/crop handling failed. Raw output preserved. |
| smoke-02 | exit 0 | exit 2 | `FAIL_AUDIT`: candidate schema mismatch and baseline image hash instability. Raw output preserved. |
| smoke-03 | exit 0 | exit 0 | `PASS_AUDIT` for one construction row; exact fixture save 1/1; first Tk KeyPress was `h` on target; first-visual frame hash verified; OCR unresolved; baseline frame integrity 0/1. |

Candidate raw SHA-256: smoke-01 `fea459487cfbba94e4f05035ca9e36415f456c651c3e8890af7dd53481dce450`, smoke-02 `991c41c22f0e627378b65ebaae27498e5a687b537ed8c198b0a9b2321e8c47ac`, smoke-03 `0ce825e857c5a7d585421b3a94308f465e4b7c89b251aa86581e704353dd7d2f`. The final audit source was rerun against the preserved smoke-03 bytes after auditor refactoring and again returned `PASS_AUDIT`, errors `[]`; this was a read-only audit repeat, not a candidate rerun.

Candidate wrapper exit receipts are `smoke-01/candidate-run-exit.txt` (0),
`smoke-02/candidate-run-exit.txt` (0), and `smoke-03/out/candidate_exit.txt` (0).
Diagnostic-only ImageMagick conversion/crop artifacts are isolated under
`construction/diagnostics/` and are not formal endpoints.

Each candidate and auditor invocation used a separate `docker run`, `--network
none`, bounded CPU/memory/PIDs, read-only container root, read-only experiment
source, and a separate output mount. The first attempt found that mounting the
parent construction directory exposed an unrelated `out/` entry; subsequent
runs mounted a dedicated empty child path. No existing container was modified.

The baseline image is captured but is not a formal gate because its XWD byte
hash changed between capture-time metadata and post-exit file inspection in
these construction probes. The first-post-key frame is the relevant image
endpoint and its bytes/hash agreed in smoke-03. Tesseract failed to resolve the
single visible `h` in the cropped sample; OCR therefore remains exploratory and
must not be treated as a validated outcome measure without a separate frozen
image-measurement method.

Commands and per-attempt bytes are retained beneath `construction/`. The
construction PASS does not establish first-character loss, readiness, user-task
performance, or any product property.
