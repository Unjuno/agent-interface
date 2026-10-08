# Issue #3676 — Docker audit-validation result

Date: 2026-09-21 (Asia/Tokyo)

Decision: `PASS_DOCKER_AUDIT_VALIDATION`

## H/T/D/C/U

- **H:** The hardened offline auditor accepts the unchanged #3675 raw only
  with its source/freeze bindings intact, rejects the predecessor's three
  mutations plus eight additional noncanonical/contradictory traces, and
  yields equivalent direct-function and CLI results in isolated containers.
- **T:** One frozen allocation from source commit
  `4ad919f773af0e788d1f7b173fd0abd0ebed5115`. The four-test suite ran once in
  one network-disabled Docker container; the raw-only CLI ran once in a second
  fresh network-disabled container. Both used the exact Git-blob source bytes.
- **D:** All four tests passed; all nine mutation controls were rejected;
  frozen raw, predecessor freeze, study freeze, original audit, hardened
  auditor, and test-source SHA-256 values matched `FREEZE.json`; the second
  container emitted `PASS_OFFLINE_STRUCTURAL_AUDIT`, `errors=[]`. Both outputs
  are retained below.
- **C:** Docker Desktop 29.8.0, Linux/amd64, kernel
  `6.6.114.1-microsoft-standard-WSL2`; image
  `python:3.12-slim-bookworm@sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a`.
  Both containers used `--network none`, read-only rootfs and source, and
  tmpfs for temporary files. The second container had only the unique output
  directory as a writable mount. No X11, GUI, input, model, or network action
  occurred.
- **U:** The allocation validates this source and finite mutation set only.
  It does not establish arbitrary audit completeness, repeat the OrbStack
  formal allocation, or broaden the XRes/product/default-runtime claim.

## Exact-source preflight stop retained

Before freezing this allocation, a read-only Docker probe used a Windows
checkout with Git `core.autocrlf=true`. The checkout transformed LF files and
the byte-binding tests correctly stopped: for example the expected predecessor
freeze hash `f40494b1…` became `03a4523a…`; the hardened source hash
`c771624b…` became `ab616622…`. Two tests still exercised mutation rejection,
but the two byte-binding/CLI equivalence tests failed. This was an invalid-byte
preflight, not an audit FAIL and not a formal allocation. The source was then
exported directly from Git objects with `core.autocrlf=false`; exact frozen
hashes were checked before the single formal run below. No evidence or source
on the existing branch was edited.

## Formal Docker execution

The frozen test container ran `python -m unittest -v`: 4 tests passed in
0.168s. Coverage includes exact predecessor raw/freeze binding; the original
three mutations; unexpected/duplicate/reordered/missing events; contradictory
bridge intent; unsupported extra fields; and direct-function versus
subprocess-CLI equivalence. The hardened auditor rejected all nine named
corruption controls.

A second fresh container ran:

```text
python audit.py evidence/raw.json --freeze evidence/predecessor_FREEZE.json \
  --study-freeze evidence/FREEZE.json --output /out/audit.json
```

It exited 0 and emitted `PASS_OFFLINE_STRUCTURAL_AUDIT` with `errors=[]`.
The retained output is `artifacts/issue3676-audit-hardening-docker-desktop-01/audit.json`.

## Retained outputs

- `artifacts/issue3676-audit-hardening-docker-desktop-01/tests.txt` — SHA-256
  `d4ebdbbb8b8e72b507afd4b15270b66598fcda93fc7f054850d151cc099d1815`
- `artifacts/issue3676-audit-hardening-docker-desktop-01/audit.json` — SHA-256
  `2cde33ff27ac67ac895d9ea1eab42a8aebadf1568545445c839927ebc07a7605`
- Exact frozen input SHA-256 values and allocation command/environment are in
  `FREEZE.json`.

The predecessor's `STOP_NOT_RUN_DOCKER_DESKTOP_DAEMON_UNAVAILABLE` remains an
accurate record of that earlier allocation. This is a later independent
Docker Desktop validation, not a rewrite of that STOP.
