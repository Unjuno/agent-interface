# Capture age survives process delivery — retained first result

**PASS_CAPTURE_AGE_BOUNDARY_SCOPED** — Issue #3953, a narrow successor to #2117/#361.
No shared runtime, earlier evidence, other branch, model or GUI-input path changed.

## Measured result

One frozen invocation produced **24/24** rows; no rerun, replacement or extension.
The independent raw-only auditor returned no errors and rejected all12 corruption
controls. Six synthetic unit tests passed before and after formal. All8 frozen
source/binary/plan/environment/construction hashes remained exact.

| Condition | Rows | Capture-age policy admits | Arrival-restamped comparator admits |
|---|---:|---:|---:|
| Prompt valid | 3 | 3 | 3 |
| Delayed, unchanged screen | 3 | 0 | 3 |
| Delayed, changed screen | 3 | 0 | 3 |
| Missing capture bracket | 3 | 0 | 3 |
| Boolean capture bracket | 3 | 0 | 3 |
| Reversed capture bracket | 3 | 0 | 3 |
| Future capture bracket | 3 | 0 | 3 |
| Stale request identity | 3 | 0 | 0 |

The three delayed-changed cases retain original target pixels while the independent
current-frame capture is clear. Restamping these packets at arrival incorrectly
admits them as fresh; retaining source acquisition time rejects all three.
The delayed-unchanged control shows that matching pixels cannot repair expired age.

Native acquisition took **0.035453–0.101663 ms** (median0.0608815 ms). Prompt frame
age at consumption was0.347912–0.386205 ms; delayed frame age was
150.477125–151.087512 ms. These are descriptive values under a deliberately imposed
>=150 ms publication barrier, **not natural transport latency, GIL attribution,
or an optimization speedup**. Both policies see exactly the same packet and time.

All24 workers exited0; all sampled keymaps/buttons were neutral, the final displayed
ROI was clear, and the owned Xvfb exited0. Model calls and GUI-input events were0.
This is a real private X-server/native-capture/pipe experiment on an authored root
ROI, not a held-out application workflow or model trial.

## Integrity and reproduction

Intake main: `b2457b746a6df06f6536585dfe2ab937aff639f4`.
Premeasurement freeze commit: `545bcd78089db9fff5c9b3bc8665820384ce0bda`.
FREEZE SHA-256: `8ff8ee83f1545a98049c2027e0a0053043302cb40e0c9fa4d9cab9bf4bbbeabc`.
The inherited native.c is byte-exact Git blob `92b2ca11117f6bcb80f45dbac62e16d62bb4f6fd`.
Raw JSONL: **71482 bytes**, SHA-256 `89d93bf75988a2cb1e3782acb2df5a4026b14bd273c0b336fd4c78dfb480a3e8`.
Raw protocol lines and full pixel bytes are retained losslessly in
`raw.jsonl.zlib.b64`; no screenshot digest substitutes for the actual pixels.

Read-only checks (no display, model, native execution or formal allocation):

```sh
python -B verify_retention.py
python -B audit.py raw.jsonl.zlib.b64 --freeze FREEZE.json --mutations
python -B -m unittest -v test_study
```

The archived native.so is for provenance; the checker decodes and hashes it without
loading it. A new live reproduction should compile native.c with the command in
PLAN.md and use a **new separately registered allocation**, never rerun the consumed
identity. Source/binary/compiler/dependency details are in ENVIRONMENT.json.
The four construction.json.zlib.b64.part01 through part04 files concatenate byte-for-byte
to the frozen construction archive (30389 bytes). The checker hashes this concatenation
in memory, even when an unfragmented local copy exists. Decode base64, then zlib,
then parse the JSON mapping relative paths to base64 original bytes. It retains original sources, exceptions, raw rows,
partials and rescue receipts. Do not execute archived failed sources.

## Retained failures and limitations

Three construction attempts remain visible: missing time-namespace proc entry;
missing inherited Xauthority; then a UTF-8-versus-bytes oracle failure with a failed
original cleanup. The third attempt's known owned Xvfb was separately terminated;
its original unknown child exit is not rewritten as clean. The fourth excluded
construction block passed. None contributes a formal observation.

The missing `/proc/self/ns/time` identity is explicit. This same-container source
uses monotonic clocks without namespace changes, and each parent/native/Python
clock enclosure passes. It does not establish cross-host clock synchronization.
The empty Xauthority file and Xvfb Unix socket are private to this execution
container; TCP listening is disabled. No host desktop or user data was accessed.

A valid age budget **does not prove unchanged semantic state or grant authority**.
The comparator is deliberately unsafe; the result does not allege a production
bug. Independent means another implementation/process, not another person. No
model-consumption receipt, held-out application, task-effect benefit, token saving,
human-tempo claim, Docker/OrbStack identity or production default is established.

## Roadmap and handoff

This bounded rung completes source reconstruction, construction, preregistration,
one formal block, raw audit, negative-evidence retention and evidence publication.
Main integration and exact remote readback are separately recorded in the PR.
The repository-wide ROADMAP remains open. **#2117 stays open** for the same-model,
load-shift, held-out-application and independent task-effect comparison; this
component PASS must not close it. That existing issue owns the next transfer
question, so no duplicate successor or automatic rerun is created.

## Publication-only incident

One native archive text transfer produced an unexpected Git blob; the mismatch
was rejected before any tree/ref update. A second exact-byte transfer matched
the expected blob. PUBLICATION_INCIDENT.json retains both IDs. No frozen source,
formal observation or gate changed. Fragmentation of the larger construction
archive is lossless storage only; its premeasurement hash is unchanged.
