# Agent Interface Research Preview — Quickstart

This RC packages the complete tracked source closure for the promoted Golden Desktop Demo v3. It is intentionally a Research Preview, not a stable cross-platform product.

## Supported preview path

The currently tested runtime target is **WSLg / Linux-X11** with Chromium plus the Windows Codex CLI bridge available from WSL. Native macOS and native Windows execution are not claimed by this RC.

The frozen RC1 default bridge requires a separately installed Windows Codex CLI JavaScript entrypoint visible from WSL. The doctor reads `AGENT_INTERFACE_WINDOWS_CODEX_JS` (default: `/mnt/c/Users/<user>/AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js`) and checks it with Windows Node.js. If that file is absent, stop at `doctor`; do not start the live acceptance run. See the [runtime setup and acquisition boundaries](../../runtime/README.md).

For a build from current source, an existing Windows Codex executable is a separate candidate bridge: see [native executable setup](NATIVE_CODEX_CANDIDATE.md). Select it explicitly with `AGENT_INTERFACE_WINDOWS_CODEX_EXE` and configure `CODEX_HOME` as described there. This does not change the frozen RC1 archive or remove the supported-host acceptance and audit gates; do not assume the candidate is present in an older downloaded archive.

## Verify the download

In the download directory, use the archive named in the release's single-entry
`SHA256SUMS` file to verify, extract and enter that version.

```bash
sha256sum -c SHA256SUMS &&
  read -r digest archive < SHA256SUMS &&
  tar -xzf "./$archive" &&
  cd "./${archive%.tar.gz}"
```

## Static first-run check

```bash
python3 release/first_run_smoke_v1/preflight.py --root .
```

This checks the packaged launcher boundary only. It does not prove GUI/model readiness.

## Install and inspect the supported host

You can run the gates individually:

```bash
./runtime/setup-golden-demo-v3.sh --install-dependencies
./runtime/golden-demo-v3.sh doctor
```

Run the setup command only when `runtime/.venv` does not already exist. The
acceptance runner reuses an existing `runtime/.venv`. If it is absent, pass
`--install-dependencies` to authorize the pinned Python package install;
without that flag the runner records setup refusal and stops before `doctor`.
This option installs only the pinned Python dependencies. It does not acquire
the Agent Interface runtime artifact, Codex CLI, Chromium, model weights, or
provider configuration. Each of those is a separate, explicit user action.

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

To authorize installation when no venv exists, add
`--install-dependencies`. `--live` separately authorizes the single fresh
golden allocation; it does not imply dependency-download consent.

The runner executes preflight, setup, doctor, retained audit, one fresh run, and `audit-live`, retaining stdout/stderr/return codes for every step. It refuses to reuse the acceptance directory and performs no automatic retry.

## What this preview does not claim

It does not claim native macOS support, native Windows support, generic Linux support, general GUI reliability, human-level operating speed, MAP01 completion, or stable API compatibility. See `SUPPORT.md` and the repository research evidence for the exact boundaries.
