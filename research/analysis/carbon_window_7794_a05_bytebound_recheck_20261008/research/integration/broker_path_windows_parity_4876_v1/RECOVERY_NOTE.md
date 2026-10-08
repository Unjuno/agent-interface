# Recovery provenance and source-identity limitation

## Original record preserved

Recovered on 2026-09-30 from [PR #4886](https://github.com/Unjuno/agent-interface/pull/4886), exact commit `ba0c477b224958238bb3430ae69810c5149c8373`, branch `research/broker-path-windows-parity-4882-20260927`. All five original files are retained byte-for-byte, including original line endings, without modifying the historical STOP or code. Their paths were absent from recovery intake main `bdd093f24c626c7ffadaa7ba2a6c8e408814675c`.

- `README.md`: Git blob `3e67ff864b96f6e0851765da5042b77c7438c44d`
- `STOP_RECORD.json`: Git blob `9771b35cdca1243be2c434d846d42e636fbe353f`
- `audit_windows_probe.py`: Git blob `c6410ebd53a5cf5b7dbfc99932baf91a786515de`
- `path_policy.py`: Git blob `cdd0e3d57e08a316fc9df6b55abca8c740db070d`
- `run_windows_probe.py`: Git blob `43b1238401563366c1d9c02bb299291d66840c8e`

The retained disposition is `STOP_SYMLINK_UNAVAILABLE`: the author reports WinError 1314 during fixture setup, exit 2, zero path cases, no formal raw output, and no independent auditor invocation. Historical local process observations are retained reports, not independently reconstructed by this recovery. Later [#5178](https://github.com/Unjuno/agent-interface/pull/5178) and [#5182](https://github.com/Unjuno/agent-interface/pull/5182) concern distinct allocations; they do not rewrite this first STOP or authorize its retry.

## Static identity finding

All five recovered Git blob identities match the source commit. The candidate resolver identity matches `candidate_blob` in the STOP record. However, the published runner/auditor bytes do **not** match the historical SHA-256 values recorded there:

- Runner: recorded `153d0008df41eb14e304409a7b191fab81490062cdee1b8696f4f876c20e140e`; published bytes `085be78a22dbc43258f33473f1b55afd33b5177964bba77cda3aa814d6d73071`
- Auditor: recorded `ea44c43ce548ae03bc1eaf6d962edbac9813540d371e7a36ffb85b56144ebd6b`; published bytes `83c8067d6e4040fc8066b6eae6d9377ee762bebdbb6e25a98ea65e855c30ac2d`

The cause is not established. No normalization, source substitution, or historical hash correction was applied. This recovery verifies the original **published** bytes, not equivalence to the exact historically executed/frozen runner and auditor. Preserve that source-identity uncertainty alongside the setup STOP.

## Scope and non-execution

Static review identifies a defensive copied-resolver fixture using a temporary synthetic tree; it does not invoke the production broker, a subprocess, model, or network target. This retention adds no cases, payloads, operational guidance, or production behavior. The three Python files were parsed as syntax only, never imported or executed. No probe, auditor, filesystem fixture, Windows privilege/security change, Docker, GPU, model, or formal allocation was run.

This is preservation of source and failure history, not a claim of Windows path safety, cross-platform parity, successful validation, or completion of Issue #4882. Any future validation requires its own authorized scope and exact source identity; missing historical evidence must not be replaced by rerunning the consumed allocation.

