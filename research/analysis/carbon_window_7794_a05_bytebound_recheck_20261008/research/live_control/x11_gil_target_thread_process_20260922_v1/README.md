# #3954: short-cue thread/process comparison — retained HOLD

Allocation `X11-GIL-TARGET-THREAD-PROCESS-20260922-001`. Parent #481; #455 / PR #479 and duplicate #493 remain unchanged. Intake base `b2457b746a6df06f6536585dfe2ab937aff639f4`. Additive evidence only; no shared runtime or default changes.

## H / T / D / C / U

**H:** At a fixed 1 ms CPython switch interval, moving an identical CPU-bound competitor from a same-interpreter thread to a separate process reduces residual acquisition gaps enough to preserve short-cue detection and verified release.

**T:** One source-first frozen block of 10 balanced pairs / 20 cases; one excluded construction pair. Native 32x32 BGRX XGetImage, exact >=512-pixel predicate, nominal 5 ms cue, 2 ms watcher cadence, 600 ms fixture-local Right-key deadline. Observer/owner/watcher/cue CPU0, competitor CPU1, Xvfb CPU2, supervisor CPU3. All first outcomes retained; no retries, replacements, extension or post-result tuning. Preformal freeze: Issue #3954 comment 5766224835. First result: comment 5766256994.

**D: `HOLD_THREAD_PROCESS_ATTRIBUTION`.**

| Frozen gate | Result |
|---|---:|
| Process detections >=9/10 | 10/10 — met |
| Median paired process/thread maximum acquisition-start-gap ratio <=0.70 | 0.31157902406584304 — met |
| Process-detect/thread-miss pairs >=2 | 1 — **not met** |
| Every source/cue/input/load/cleanup/raw-integrity gate | 20/20 — met |

Thread detections: 9/10. Retained acquisitions: 1,398. Actual cue exposure: 5.077759–5.235687 ms (allowed 4–8 ms). App press/release: 1/1 in every case; terminal keymaps empty and final ROI clear. All case processes exited 0; process loads exited without forced termination; private Xvfb was reaped.

Independent raw auditor: `PASS_RAW_INTEGRITY_SCOPED`, 15/15 corruption controls rejected. Inherited auditor: identical scientific HOLD, counts and ratio, 14/14 controls rejected. Integrity PASS is not scientific PASS.

**C:** Thread/process also changes address-space/interpreter sharing. Guest affinity is not physical-host isolation; Linux scheduling and X11/Tk may dominate. Detection ends sampling, so maximum-gap ratios have unequal observation-window exposure and are not general latency speedups.

**U:** Provided Linux x86_64 execution container, CPython 3.13.5 with GIL, existing Tk/Xlib/Xvfb/gcc. Docker CLI and direct DNS unavailable; image identity unknown. No Docker/OrbStack equivalence, real-desktop/task benefit, model utility, production architecture or default-switch claim. All input was confined to a new private Xvfb with TCP disabled. No provider/network/user desktop/shared runtime action.

## Retained construction failure

The initial independent auditor rejected the inherited exact missing-Xauthority stdout warning. Original source, plan, raw and STOP stderr are preserved in the bundle. Before formal, the auditor was changed to allow only that exact warning; stderr and other output remain rejected. Offline re-audit of the same raw passed; no live rerun or scientific gate change. Missing python-xlib distribution metadata and the native compiler warning are also documented. All three rebuilt native binary hashes equal the predecessor; whole-runtime equivalence is not implied.

## Reconstruct and audit without another live run

The seven text parts are transport-only fragments of one XZ archive, not separate experiments. `parts.json` binds their bytes, SHA256 and Git blob IDs. The decoded bundle is 49,028 bytes, SHA256 `3d0ea8172d6e6777da51e42a5f3c088135763e8462d63323b6e55058ba8ac6a6`. It contains 83 files including original source/binaries, preregistration, environment, all construction/formal raw and case records, both auditors, controls, process receipts, first STOP and full RESULT.md.

```sh
python unpack.py /tmp/issue3954-evidence  # destination must not exist
cd /tmp/issue3954-evidence
python audit.py formal01/raw.json
python test_audit.py formal01/raw.json
python - <<'PY'
import json
from pathlib import Path
from independent_audit import check
raw = json.loads(Path('formal01/raw.json').read_text())
plan = json.loads(Path('prereg.json').read_text())
print(json.dumps(check(raw, plan, formal=True), indent=2))
PY
```

`unpack.py` verifies every fragment, decoded archive and member before writing; it does not load native binaries or start X11. `verify.py formal01/raw.json --formal` additionally checks absolute runtime/source paths against the recorded environment, and should refuse a different environment. Do not relax that check to claim historical runtime equivalence. The portable raw-only check above makes no current-runtime identity claim.

Formal raw SHA256: `3e5af6ecc88b2dc66fbffeb43d5c8c2c9ca4bcc056be9c9e7bf5834b5c0fe99a` (507,136 bytes). Preregistration SHA256: `5cc2b05ce81fbe2565daaf902d5d8ddb663a74657d19dd198484dd34889b2677`.

A fresh local unpack verified all 83 members; both auditors and all 29 corruption controls passed again on reconstructed bytes. This was offline verification, not another experiment. Repository-wide tests were not run because a full checkout was unavailable. RESULT.md's `[all local Python sources]` compile line is shorthand for iterated `py_compile`, not a literal shell command.

## Roadmap / handoff

Source recovery, collision check, H/T/D/C/U, excluded construction, preformal freeze, one formal block, raw audit and full retention are complete. PR integration is evidence-only and does not promote the mechanism. Keep the original HOLD and older Issues/results unchanged.

A new separately preregistered successor could measure identical fixed read-only observation windows after release in both arms to remove detection-dependent sample-count confounding. It would require a new allocation and must not extend this one. No such follow-up has run. The broader integration spine (#2789), same-model utility, real desktop comparison, transfer and human-tempo ROADMAP are not completed by this component result.
