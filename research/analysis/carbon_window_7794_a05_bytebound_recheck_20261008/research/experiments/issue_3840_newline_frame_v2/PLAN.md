# Issue #3840 — valid-JSON strict prefix after terminal-LF loss

Allocation: `issue3814-jsonl-frame-02` (successor to stopped #3814 Formal-01)

## H / T / D / C / U

**H** — The CLI emits newline-terminated compact JSON. Removing only the final LF produces a strict prefix that a JSON-parser-only caller accepts as a completed result. A caller that validates JSONL framing rejects it and can recover the exact retained report via read-only `attempt-status` then `review`, without redispatch.

**T** — Frozen runtime-source base main `5842cea6b16dde275f79caef3f09fdba828112e0`. Run one source-read-only, network-disabled Docker Desktop Linux/amd64 container against the public CLI `main()` with a synthetic dispatch facade. The runner inserts `/source` into `sys.path` before importing the package, and the exact command also sets `PYTHONPATH=/source`. Capture complete producer bytes, then deliver exactly `accepted[:-1]` to the caller. Compare complete delivery, parser-only interpretation, terminal-LF-aware interpretation, and actual read-only status/review recovery. Add request-only and occupied-destination controls. Retain accepted/delivered bytes, all hashes, parsed outputs, attempt snapshots, dispatch counts, source manifest, and image ref. Independently run the raw-only auditor once in a separate network-disabled container with evidence mounted read-only.

**D** — `FAIL_FALSE_SUCCESS` if the JSON-parser-only caller accepts the no-LF strict prefix as completed; `PASS_FRAMING_GUARD_RECOVERY_SCOPED` is permitted only if the frame-aware guard rejects it, recovery returns the exact retained report read-only, dispatch remains exactly once, and all controls plus independent audit pass. If parser-only acceptance and the recovery guard both behave as expected, report the overall false-success finding and the secondary guard/recovery result separately; do not erase the finding with the guard result. `STOP_SETUP` for source/image/container mismatch; `HOLD_EVIDENCE_INCOMPLETE` for unbound bytes or audit mismatch. One formal allocation; no retries or post-hoc edits.

**C** — Docker Desktop Docker Engine `linux/amd64`; platform-specific official Python image `python@sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b`; `--network none`, read-only root/source, fresh separate output directories, 1 CPU, 512 MiB, 64 PIDs, all capabilities dropped, no-new-privileges. Synthetic dispatch facade only. No GUI, display, model/provider, native input, or production changes. This is not OrbStack parity.

**U** — One deterministic local CLI framing boundary and retained-recovery path. Not real OS/network truncation, live task, broad caller reliability, power-loss, performance/token evidence, or closure of #3711/#3808. The no-LF parser-only result is a scoped consumer-contract finding, not evidence that JSON syntax itself is corrupt.

## Frozen provenance

- Base commit: `5842cea6b16dde275f79caef3f09fdba828112e0`
- Docker Engine platform: `linux/amd64`
- Image platform manifest: `sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b`
- Expected formal disposition: `FAIL_FALSE_SUCCESS` when parser-only accepts; secondary `PASS_FRAMING_GUARD_RECOVERY_SCOPED` requires strict framing rejection, exact report recovery, no replay, controls, and audit.

Frozen Linux-container bind-mount source SHA-256 values (Windows checkout runtime bytes; canonical LF-normalized identities are also recorded in `raw.json`):

- `runtime/cli_v1/__main__.py`: `39d493b7e5c8c3ba56573775024419e8cdcfcdae5c70ea75b984461f2c17f89a`
- `runtime/cli_v1/api.py`: `07cddfde5752ff99f68ddf4a8044c799246fc2b8edcfa77453195e6b9d27a9bd`
- `runtime/cli_v1/attempt.py`: `6aed46cfd16e6718e890153d58a541735c73b62ed3f86775e29aa4cebf81fcd2`
- `runtime/cli_v1/observe.py`: `75a0c9033bb500d1de15e0479904c7bd19b9aef25a3d30142667b3eaaf58b60e`
- `runtime/cli_v1/receipt.py`: `345457cf73f78a67f19448eaaad37375d10da9fed7af9e73d24392f047acc1e3`
- `runtime/cli_v1/receipt_image.py`: `1d6135011e001c724e636f742822984ecebc560696e980a7a98215133d604691`
- `runtime/cli_v1/receipt_references.py`: `987beb82dc573777721719a8d7436954768d90ed5cfc9b8483f515a8593fbb5b`
- `runtime/cli_v1/review.py`: `8f4569809e811c98406c0ba878c7453be5745d2b6281ec4a6bf1ad7cb40a4d96`
- `runtime/cli_v1/test_cli.py`: `7abfbff6a89b60d2c9263d69ffae564a9691f468ca1e9e5ce5c36e5d38fcd58b`
- `runtime/selector_v1/__init__.py`: `cff57f1b8f651ba38f4f160189dc2bc55cabf5b1dcc4fb95a45458e1da6c3128`
- `runtime/selector_v1/selector.py`: `fc10f4b31fed30f11eb347528e056f5786b656c430346124724a51876828d93a`
- `runtime/motor_state_v1/__init__.py`: `862c144678c3a1b12647a5dc2049a64b8a2af4bb9415b4d28bcae386fbfde384`
- `runtime/motor_state_v1/adapter.py`: `3f1a5e664a013a97fb8504fea2ac637098c24e3f262db7d4c8cab8705b51f59e`

The original plan/runner/auditor hashes and exact commands were posted to Issue #3840 before formal execution. The immutable `raw.json` embeds all source hashes and the runner/auditor hashes. The separate initial audit output reports four rows, `errors: []`, and `PASS_AUDIT_NEWLINE_FALSE_SUCCESS_SCOPED`. A later independent raw-only cross-check corroborates row semantics. After the run, the audit script and plan were edited during an invalid comparison attempt; their exact frozen byte snapshots were not committed. Consequently the raw result and initial audit remain retained, while independent re-execution of the exact preregistered audit/provenance bundle is not established (`HOLD_EVIDENCE_INCOMPLETE`). No formal rerun.
