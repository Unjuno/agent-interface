# Agent Interface Research Preview — Quickstart

This RC packages the complete tracked source closure for the promoted Golden Desktop Demo v3. It is intentionally a Research Preview, not a stable cross-platform product.

## Supported preview path

The currently tested runtime target is **WSLg / Linux-X11** with Chromium plus the Windows Codex CLI bridge available from WSL. Native macOS and native Windows execution are not claimed by this RC.

## Verify the download

From the directory containing the archive and `SHA256SUMS`:

```bash
sha256sum -c SHA256SUMS
```

Extract and enter the directory:

```bash
tar -xzf agent-interface-research-preview-*.tar.gz
cd agent-interface-research-preview-*
```

## Static first-run check

```bash
python3 release/first_run_smoke_v1/preflight.py --root .
```

This checks the packaged launcher boundary only. It does not prove GUI/model readiness.

## Install and inspect the supported host

You can run the gates individually:

```bash
./runtime/setup-golden-demo-v3.sh
./runtime/golden-demo-v3.sh doctor
```

Or retain the whole supported-host prefix in one new evidence directory:

```bash
python3 release/preview_bundle_v1/accept_supported_host.py \
  --out artifacts-local/release-acceptance-prefix
```

`doctor` must pass before a live run. If path discovery is ambiguous, set the environment variables documented in `runtime/README.md`.

## Reconstruct the retained benchmark

```bash
./runtime/golden-demo-v3.sh audit-retained
```

This archive contains the complete tracked RC closure specifically so the retained audit is not dependent on a reduced research bundle.

## Fresh preview run

For final supported-host acceptance, explicitly consume one no-retry live allocation:

```bash
python3 release/preview_bundle_v1/accept_supported_host.py \
  --live \
  --out artifacts-local/release-acceptance-live
```

The runner executes preflight, setup, doctor, retained audit, one fresh run, and `audit-live`, retaining stdout/stderr/return codes for every step. It refuses to reuse the acceptance directory and performs no automatic retry.

## What this preview does not claim

It does not claim native macOS support, native Windows support, generic Linux support, general GUI reliability, human-level operating speed, MAP01 completion, or stable API compatibility. See `SUPPORT.md` and the repository research evidence for the exact boundaries.
