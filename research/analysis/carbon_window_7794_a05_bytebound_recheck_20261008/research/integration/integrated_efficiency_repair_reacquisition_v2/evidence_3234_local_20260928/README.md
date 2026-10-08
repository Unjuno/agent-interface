# Local retained-result provenance re-acquisition

This evidence package corresponds to GitHub Issue #3234 and current-main source commit `821482e56d5e0e4557fda86da53c12dd44d0e012`.

## H / T / D / C / U

- **H:** The retained v1 fixture and result agree with the v2 provenance gate and independently reconstructed raw accounting.
- **T:** The current-main gate was run once in local Docker Desktop `desktop-linux` using Python 3.12 image `python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`, Linux/amd64, `--pull=never --network none --read-only --cpus=0.25 --memory=256m --pids-limit=32 --cap-drop=ALL --security-opt=no-new-privileges:true`. Source and inputs were mounted read-only. Exact inputs, source, gate stdout and independent audit output are retained in this directory; see `MANIFEST.sha256`.
- **D:** Gate output: `PASS retained-result provenance gate`. The separately structured audit recomputes all eight ratios directly from raw JSON and checks schema/task/comparator identity plus historical `formal_invocation=1` and `formal_reruns=0`. All checks match `RESULT.json`.
- **C:** The first mount layout did not preserve the relative parent path expected by the gate and failed before reading the fixture. No bytes were changed. A minimal read-only bundle with the expected directory shape was then used for the successful gate and audit.
- **U:** This is a local provenance/accounting validation, not GitHub Actions attestation or fresh model/provider allocation. It establishes no live model utility, GUI/task effect, latency, token benefit, or integrated composition result.

The raw input/source files under `raw/` byte-match their current-main Git blobs: fixture `a969971e32003b29505063c8d1ab34966fc7ed23`, result `bf7fb72fe43e815f1d5d13f682a585de29ffed7d`, checker `f2a00a343d42b8213087634a58595946883bc7ed`, and test `88825094059c896b52e50e9432eccf956840460a`. The predecessor result and historical CI run remain unchanged.
