# #6081 S1 / S2 runner STOP preservation

## Archival disposition

This package preserves the complete committed source and first runner STOP evidence of two separate allocations. Both remain **NOT_EVALUATED**. It does not retry them, validate the proposed method, or promote a process exit code to a scientific result.

| Record | Immutable head | Preserved disposition | Actual execution |
|---|---|---|---|
| S1 `INTENT-SLOT-6081-T0-20261001-01` | `acdc4e11a41f4b6c6831b4c47dbd8610dbf3b1ed` | `STOP_RUNNER_ARGUMENT_BINDING` | One candidate-side and one audit-side Python wrapper launched with empty argv; both exited 0 in the interactive interpreter. Candidate and auditor scripts did not run. |
| S2 `INTENT-SLOT-6081-T0S2-20261001-01` | `2c3d42638937ecc2465e3401388371900298d19f` | `STOP_RUNNER_SOURCE_NOT_MATERIALIZED` | Candidate CLI launch attempted once with intended argv; Python exited 2 because candidate.py was absent from the execution directory. Scientific module executions 0; auditor attempts 0. |

The empty stdout files are intentional retained evidence, not omitted output. `candidate.json` and `audit.json` are absent from both original packets; none is manufactured. The source files exist in Git, which does not establish that they existed in the historical execution working directory. The original FREEZE formal-invocation counts describe the planned budget; actual execution is recorded in RUN_FAILURE and process receipts.

## Sources and coordination

- [S1 registration](https://github.com/Unjuno/agent-interface/issues/6081#issuecomment-5932769094)
- [S1 first STOP and exit-code correction](https://github.com/Unjuno/agent-interface/issues/6081#issuecomment-5932838653)
- [S2 prospective runner-repair registration](https://github.com/Unjuno/agent-interface/issues/6081#issuecomment-5932891029)
- [S2 first source-materialization STOP](https://github.com/Unjuno/agent-interface/issues/6081#issuecomment-5932935740)
- [Later S4–S7 result and scoped limits](https://github.com/Unjuno/agent-interface/issues/6081#issuecomment-5943052770)

These packets are distinct from already merged PR #6087's 10-case unsafe-schedule diagnostic, #6091's invalid-baseline STOP, and #6357's S4–S7 successor chain. Their rows/outcomes are not pooled, rescored or replaced. S3 is another separate frozen branch and is not included in this preservation package. Issue #6081 remains open for its broader real-actuator/live questions. No active allocation is claimed or released here.

## Exact-byte preservation

[MANIFEST.json](MANIFEST.json) maps all 24 original paths to `original/<source_path>`, original branch/head, Git blob, byte length and SHA256. S1 has 13 files / 33,363 bytes; S2 has 11 / 32,606 bytes. Total 65,969 bytes, 16 distinct blobs. Their five source files are intentionally shared byte identities. CRLF process receipts and all captured stdout/stderr are retained unchanged.

[HISTORY.json](HISTORY.json) accounts for both two-commit histories: each contains one source freeze and one additive STOP record. All changed files were additions, and every historical added blob remains identical at its branch head. No intermediate version is omitted and no source commit ancestry is merged by this archive. The original refs remain untouched.

[VERIFICATION.json](VERIFICATION.json) records static checks only:

- All 24 files match their immutable Git blob IDs and byte sizes
- All 10 source SHA256 entries in the two freezes match
- All six stdout/stderr sidecars equal the corresponding decoded receipt fields byte-for-byte
- S1 process receipt SHA256 `c41fabfb17b5273b21c314d4d618b8e9730c09fd99b5a0e709a988ab01833018`
- S2 process receipt SHA256 `81f85910c9cb0201236833a58b0e7adc539b89a20db99661cbf84d1b4f57b10b`

These checks prove retained-byte consistency, not independent authentication of the historical host, execution or scientific correctness. Historical construction/canary PASS statements remain original statements; they were not rerun here.

For an independent static identity check, from this directory run:

```python
import hashlib, json, pathlib
root = pathlib.Path('.')
for item in json.loads((root / 'MANIFEST.json').read_text())['entries']:
    data = (root / item['archive_path']).read_bytes()
    assert len(data) == item['bytes']
    assert hashlib.sha256(data).hexdigest() == item['sha256']
    assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == item['git_blob']
print('24 preserved files verified; no research source executed')
```

## Publication and safety boundary

Publication base main: `43f7cd88d91af05036fae2100ec4e155c59e105c`. Both original paths were absent at inspection; the new package is nevertheless placed in the existing `research/archive/` namespace to preserve allocation separation and avoid changing active paths. No runtime, shared source, workflow or index file is modified. No source ref restoration, tag or deletion is performed for this archive.

[WORKFLOW_SAFETY.json](WORKFLOW_SAFETY.json) records all 227 exact current-main workflow identities and event/path checks. Archive paths match no push workflow, the broad create and formal PR jobs have false exact-other-branch guards, and opening this Draft may run the existing deterministic replay unittest. No consumed research allocation is dispatched. Exact-head remote readback, hosted check results and independent preservation review remain separate handoff gates.

Rescue execution counts: candidate 0, auditor 0, construction tests 0; no GUI, model, GPU, Docker/WSLc experiment or scientific rerun. This is preservation of STOP evidence for later review, not a method PASS or permission to retry S1/S2.
