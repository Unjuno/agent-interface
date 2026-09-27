# Issue #4242 — first formal outcome

**Disposition: `STOP_FIXTURE_PIXEL_CAPTURE_BADMATCH_BEFORE_BRIDGE`.**

The sole frozen formal workflow invocation was GitHub Actions run `35820869111` at exact PR head / source commit `ca58713dd8561011b428054123df99373626f3d9`. The workflow itself concluded failure. **No formal retry/replacement is authorized or performed.**

## What completed

- exact PR-head checkout succeeded;
- Ubuntu 24.04 runner setup succeeded;
- Xvfb/Openbox and pinned Python-Xlib/Pillow installation succeeded;
- exact source/environment provenance files were emitted;
- the formal Python process started once.

## Stop boundary

The first case stopped in `App.pixels()` before `NativeHandleBridge(...)` construction. Openbox had already reparented/mapped the raw Xlib client window, and the direct client-window `GetImage` returned X11 `BadMatch`.

Trace boundary:

```
Xlib.error.BadMatch
experiment.py -> one_case -> app.create -> app.pixels -> window.get_image
```

The failure occurred **before bridge construction, observation, alias mint, guarded dispatch, XTEST input, or application effect**. Therefore formal rows = 0/12 and this is setup/fixture evidence, not evidence for or against the #4242 hypothesis.

No `RAW.json`, `AUDIT.json`, or corruption-control result was produced. The workflow's `set -e` exited at the formal command, so no fabricated `FORMAL_EXIT` file is claimed. The GitHub job itself records the command failure as exit 1.

## Retained evidence

Workflow artifact `10733985477`, digest `sha256:0d20665eed4596a89a2cae28fa55496a33f07ac13576b11ed57cbe0fea0a3f16`, contains the exact available first-outcome evidence:

- `formal.stdout`
- `formal.stderr`
- `SOURCE_COMMIT`
- `SOURCE_SHA256SUMS.txt`
- `ENVIRONMENT.json`
- Xvfb/Openbox version outputs

A base64 copy of that exact artifact ZIP is retained in this directory so the evidence does not depend on Actions artifact expiry.

Observed environment: GitHub hosted Ubuntu 24.04.5 / runner image `ubuntu-24.04 20260907.300.1`, Linux 6.17.0-1022-azure x86_64, Python 3.12.3, Python-Xlib 0.33, Pillow 11.3.0, Openbox 3.6.1.

## H/T/D/C/U status

- **H:** unchanged and unmeasured.
- **T:** one frozen allocation was consumed; stopped before row 1.
- **D:** typed STOP, no scientific PASS/FAIL.
- **C:** direct client-window GetImage after Openbox reparenting was an invalid fixture assumption. #777's actual lifecycle logic is not contradicted.
- **U:** the actual NativeHandleBridge composition remains open. A future allocation under the same scientific question would need construction that exercises the exact Openbox client/capture topology before a separately frozen new allocation. This STOP must remain immutable.

No runtime/default source is changed by this result.
