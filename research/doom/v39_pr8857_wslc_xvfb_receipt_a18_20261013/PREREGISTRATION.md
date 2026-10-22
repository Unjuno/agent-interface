# PR #8857 actual-Xvfb receipt bridge A18 — preregistration

## H/T/D/C/U

- **H:** The PR #8857 per-key receipt adapter and analyzer will produce a complete verified trace for one actual X11 `w` down/up through the unmodified V10 owner, with an independent Xlib client observing KeyPress/KeyRelease and server keymap down/up.
- **T:** One private TCP-disabled Xvfb display, one focused client window, one `w` down and one explicit `w` up through PR #8857's V3 wrapper over V10. Record the client event pair, independent XQueryKeymap state during hold/after up, receipt JSON, owner terminal state and exact source/image identity. One WSLc candidate invocation; no retry. Run a separate read-only auditor over saved raw afterward.
- **D:** `PASS_METHOD_SCOPED` only if matching X11 press/release and down/up keymap states are observed, owner closes with a verified empty receipt and stopped thread, analyzer says ready with one hold, and raw/source integrity checks pass. If X11 release is verified but analyzer rejects the trace, record `FAIL_ANALYZER_BRIDGE`; missing/mismatched event/state is `FAIL_X11`; setup/harness error is `STOP`. No result will be relabeled.
- **C:** Xvfb/XTEST and an empty focused X11 window do not establish physical keyboard state, target-application consumption, game effect or desktop behavior.
- **U:** No model, Doom/MAP01, threat, useful feedback, recovery efficacy, physical keyboard or live allocation. Requested memory is not a hard cap; WSL swap enforcement is unsupported.

## A17 delta

A17 was retained as `STOP_HARNESS_EVENT_FIELD`: its one candidate invocation admitted `w` but raised while reading `event.id`, before its event observer or explicit up. A18 changes only the Xlib event field access to `window`, uses a new intent token and captures owner terminal state in `finally`; A17 source, raw, disposition and output remain unchanged. A preflight introspection of `KeyPress._fields` raised `TypeError` because `_fields` is a `Struct`, not an iterable; this was a tooling probe only and is preserved under A17 `results/preflight-01/`.

## Frozen source/runtime

- PR #8857 head: `4536ebff7d71848dc86fbf1cdc4f54957eb9ce2d`; base `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
- Image ID: `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592` (`a09-owner-close-xvfb:20261012`, Python 3.14.8 linux/amd64, Xvfb and Xlib/XTEST preflighted).
- WSLc 3.0.1.0, `--pull never --network none --cpus 1 --memory 512M --user 65534:65534`, read-only `/src`, separate writable `/out`, `--rm`.
- Single output `results/a18-01/raw.json`; container name `codex-wslc-pr8857-xvfb-a18-20261013`.

## Exact command

```powershell
wslc run --rm --name codex-wslc-pr8857-xvfb-a18-20261013 --pull never --network none --cpus 1 --memory 512M --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume "<study>/INPUT:/src:ro" --volume "<study>/results/a18-01:/out:rw" --workdir /src/research/doom sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592 python experiment_candidate.py
```
