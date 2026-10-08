# Mindustry live-smoke asset readiness v1 — retained first outcome

Task: `MINDUSTRY-LIVE-SMOKE-ASSET-READINESS-20260917-001`  
Issue: #879  
Immutable BASE: `1e42633af36a2c6307df511754c1a9792061cb32`

Disposition: **`HOLD_ASSETS_NOT_MATERIALIZED`**.

The source-first frozen disposable-container formal runner was invoked exactly once; formal reruns were zero. The independent auditor passed every check and four corruption controls were all rejected. No provider/model call, GUI, Mindustry process, X11 task input, network task action or user-data action occurred.

## Provenance closure

The repository pin is not a custom or patched game JAR. `research/benchmark_discovery/assets.json` renames Anuken's official v160.2 `Mindustry.jar` to `Mindustry-v160.2-complete.jar` without changing the bytes:

- official release/tag: `v160.2` / release id `387649509`;
- official asset id: `559668837`;
- size: `87,022,576` bytes;
- SHA-256: `7f210295dfffb4c17b582b27bab41f4dde83f557f00f0877572fdac943f40539`;
- repository asset-manifest Git blob: `fcbe570ea55ad92ed95a132e487a205cb61c39ff`.

The retained canonical save is separately identified by Git blob `7663b25633d853a257fbb407723fe85579120111` and SHA-256 `8fff67b0c130ee59a3838c92754b73225a506902bd4838dcc3f1fb5be286cbed`.

All frozen provenance gates pass.

## Current container readiness

Generic execution prerequisites are present:

- Xvfb `/usr/bin/Xvfb`;
- Openbox `/usr/bin/openbox`;
- wmctrl `/usr/bin/wmctrl`;
- OpenJDK 21.0.11;
- Pillow 12.3.0;
- python-xlib 0.15;
- NumPy 2.3.5;
- openpyxl 3.1.5.

The bounded candidate paths contain neither the exact pinned JAR nor the exact canonical save. Therefore `environment_ok=true`, `jar_ready=false`, and `save_ready=false`.

This is a materialization HOLD, not a runtime or interface failure.

## Integrity

- source-first freeze commit: `653504d5d5827cbf5a6c6d572d78733251367d8a`;
- formal invocation: 1; reruns: 0;
- RESULT SHA-256: `30593914b8ed6fa46e46c842fb1e55bac8af49971bd64d2b5dcb32e360387fdd`;
- AUDIT SHA-256: `c594aa107535cc4c0b7560a9ab99a24944cedba9e37ed276051bd6968e7a0606`;
- CORRUPTION SHA-256: `3ead55ce8e01bff67587d3f6444e75dddac2453480c1e2093708d66d3e21069d`.

## Boundary / successor

The next step is not another synthetic Agent Interface mechanism. A coordinator or execution environment must materialize exactly these two frozen assets into the live-smoke container and grant the separately scoped zero-model GUI/Mindustry lease. Once both hashes verify, rerun under a **new study ID**; do not rerun this HOLD allocation. Only after the zero-model repeat/reset fixture smoke passes should the final #57 same-model three-arm allocation be preregistered.
