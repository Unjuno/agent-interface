# Frozen conditions — WSLc local runtime smoke

- Source main: `e5866db03e25c044f7ffead5118624a1cd8c33e9`.
- Source script: `.github/scripts/test_wslc_local_runtime.ps1`, SHA-256
  `ae48bae789655ea192dba7ad9fc20e62ef44635f447afd8c56123a7cb770f4d6`.
- Bounded-process module: `.github/scripts/wslc_bounded_process.psm1`, SHA-256
  `69525dde85cffd189301890f86314fefb5ff4b2e9882f711634daad48490ee57`.
- Host: Windows `10.0.26300.9974`, PowerShell `7.6.9`, WSL/WSLc `3.0.5.0`.
- Freeze/run window: 2026-11-21 12:21–12:24 UTC. The prior read-only process
  snapshot at 12:19:50Z observed zero `wslc.exe` processes. A post-run session
  note at 12:24:29.921Z also reported zero; its raw process output was not
  retained. Neither observation establishes owner release or global container
  state.
- Invocation: one run of `test_wslc_local_runtime.ps1` with CLI timeout 10 s,
  run timeout 90 s, and cleanup-query timeout 15 s.
- Image: `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`;
  `--pull never`, `--network none`, `--rm`, `--cpus 1`, requested `--memory
  512M`, and a GUID-named read-only bind mount.
- Scope: one bounded WSLc compatibility smoke. The script queried only the
  exact generated container ID for cleanup; it did not enumerate unrelated
  containers. No Docker command, model/provider call, GUI action, or WSL
  restart occurred.

The original runner conditions are retained verbatim at
`raw/runner-conditions-as-written.md`. That file contains literal `$main`,
`$scriptHash`, and `$moduleHash` placeholders and a malformed script path due
to a tab conversion. This corrected transcription is based on the captured
invocation summary and the source hashes above; it does not replace or alter
the original file. The runner summary's `conditions_sha256` therefore hashes
the malformed original, not this corrected transcription.
