# Issue #3814 — valid-JSON strict prefix after terminal-LF loss

## H / T / D / C / U

**H** — The CLI emits newline-terminated compact JSON. Removing only the final LF produces a strict prefix that a JSON-parser-only caller accepts as a completed result. A caller that validates JSONL framing rejects it and can recover the exact retained report via read-only `attempt-status` then `review`, without redispatch.

**T** — Frozen base main `c215b11fc9609ec02810a22317c926374f399858`. Run one source-read-only, network-disabled Docker Desktop Linux/amd64 container against the public CLI `main()` with a synthetic dispatch facade. Capture complete producer bytes, then deliver exactly `accepted[:-1]` to the caller. Compare complete delivery, parser-only interpretation, terminal-LF-aware interpretation, and actual read-only status/review recovery. Add request-only and occupied-destination controls. Retain accepted/delivered bytes, all hashes, parsed outputs, attempt snapshots, dispatch counts, source manifest, and image ref. Independently run the raw-only auditor once in a separate network-disabled container with evidence mounted read-only.

**D** — `FAIL_FALSE_SUCCESS` if the JSON-parser-only caller accepts the no-LF strict prefix as completed; `PASS_FRAMING_GUARD_SCOPED` is permitted only if the frame-aware guard rejects it, recovery returns the exact retained report read-only, dispatch remains exactly once, and all controls plus independent audit pass. If parser-only acceptance and the recovery guard both behave as expected, report the overall false-success finding and the secondary guard/recovery result separately; do not erase the finding with the guard result. `STOP_SETUP` for source/image/container mismatch; `HOLD_EVIDENCE_INCOMPLETE` for unbound bytes or audit mismatch. One formal allocation; no retries or post-hoc edits.

**C** — Docker Desktop Docker Engine `linux/amd64`; platform-specific official Python image `python@sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b`; `--network none`, read-only root/source, fresh separate output directories, 1 CPU, 512 MiB, 64 PIDs, all capabilities dropped, no-new-privileges. Synthetic dispatch facade only. No GUI, display, model/provider, native input, or production changes. This is not OrbStack parity.

**U** — One deterministic local CLI framing boundary and retained-recovery path. Not real OS/network truncation, live task, broad caller reliability, power-loss, performance/token evidence, or closure of #3711/#3808. The no-LF parser-only result is a scoped consumer-contract finding, not evidence that JSON syntax itself is corrupt.

## Frozen provenance

- Base commit: `c215b11fc9609ec02810a22317c926374f399858`
- Docker Engine platform: `linux/amd64`
- Image platform manifest: `sha256:44ff437bba879d4941b710a369a8f19266aea34b29002807f0c487fabc9eec9b`
- Expected formal disposition: `FAIL_FALSE_SUCCESS` when parser-only accepts; secondary `PASS_FRAMING_GUARD_RECOVERY_SCOPED` requires strict framing rejection, exact report recovery, no replay, controls, and audit.

Frozen Linux-container bind-mount source SHA-256 values (Windows checkout runtime bytes; canonical LF-normalized identities are also recorded in `raw.json`):

- `runtime/cli_v1/__main__.py`: `35fca27a88ae0342a431297ffce9360557d7abdaa0acc6ce0f1ecfdc8aa2028e`
- `runtime/cli_v1/api.py`: `486c2e6ce8ed9ccbfef95e1172bbe8a8bee8314223102c0e3cbc48ee184665ad`
- `runtime/cli_v1/attempt.py`: `1a30c92c9b520bbfa7db390f8af82ff455dd91ffa177ce3b288d7374b3150178`
- `runtime/cli_v1/observe.py`: `13a165fffc8e6148f68ca8cd81aab4ce429c41e4d13d5574169f9784874d6580`
- `runtime/cli_v1/receipt.py`: `ee237b1481f6ffc07dd60cc3c8f074be800bd7fff389f565b7237853a013962b`
- `runtime/cli_v1/receipt_image.py`: `045fece398694fb70541518368ffd5891d57c06ee786e1c40a397a17a53af543`
- `runtime/cli_v1/receipt_references.py`: `9db9e79d43670d361631715cf621a06cff880d9a4f442be345b0ad2815f98017`
- `runtime/cli_v1/review.py`: `0729242fc2168368b54bb7bfbe1227defd140e1f8dd8cd7152e112b7bda6b288`
- `runtime/selector_v1/__init__.py`: `3e4f381f3b8ed95c05382e1f8e03c1c3b55225dea1e012fbf12b8a72b01d789d`
- `runtime/selector_v1/selector.py`: `6e9d8d0e33ffe4a8df7bb4200013c498bb0dc80d30aca47b36d78cb494b4da2d`
- `runtime/motor_state_v1/__init__.py`: `d66dd7f44d8e9678d910eedc77f5bca73e9e047b7f995bdfe17216e5c0f89905`
- `runtime/motor_state_v1/adapter.py`: `4f798c61f4a0ab8a64feb93508469ddaa6148ffc1a427df080374b0318d2e540`

The source file digest inventory is embedded in formal `raw.json`; runner and auditor are frozen by their Git blobs at this plan commit. The plan, runner and auditor hashes, expected outcomes, and image are posted to Issue #3814 before formal execution. No formal run starts before that freeze record exists.
