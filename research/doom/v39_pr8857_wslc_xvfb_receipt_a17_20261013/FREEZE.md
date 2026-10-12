# V39 PR #8857 actual-Xvfb receipt bridge A17 — freeze

## H/T/D/C/U

- **H:** The PR #8857 `InputTransitionOwner v3` admission receipt and direct-retention analyzer will accept one actual X11 key down/up through the unmodified `InputOwner v10` implementation, while an independent Xlib client observes the matching KeyPress/KeyRelease and keymap down/up states.
- **T:** One `w` down/up on one private, TCP-disabled Xvfb display. Use the exact PR #8857 base/head and byte-pinned `input_owner_v10.py`, `input_transition_owner_v3.py`, `executor_v3.py`, `lease.py`, analyzer, and candidate. One WSLc container invocation; no retry. Independent host auditor checks saved raw output and hashes.
- **D:** PASS only when the matching X event pair and server keymap transitions are observed, owner closes with verified empty state and stopped thread, and analyzer returns `measurement_ready=true` with one valid hold. Preserve FAIL/STOP otherwise. A physical X11 key-up with rejected/incomplete analyzer receipt is a scoped bridge failure, not an X11 release failure.
- **C:** Private Xvfb, XTest, and an empty focused X11 window may behave differently from a desktop or application. Event/keymap observation and caller timestamps do not provide physical keyboard sensor state or game effect.
- **U:** No model, Doom, MAP01, physical keyboard, useful task feedback, threat exposure, recovery benefit, or live allocation. WSLc memory request is not a hard cap; swap enforcement is unsupported on this host.

## Frozen inputs

- PR #8857 head: `4536ebff7d71848dc86fbf1cdc4f54957eb9ce2d`.
- PR base/current main at PR creation: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
- WSLc image tag: `a09-owner-close-xvfb:20261012`, immutable local ID `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592` (locally cached image; no pull).
- Container controls: `--pull never --network none --cpus 1 --memory 512M --user 65534:65534`, read-only `/src`, writable output-only `/out`, disposable container named `codex-wslc-pr8857-xvfb-a17-20261013`.
- One expected result path: `results/a17-01/raw.json`; no retry or overwrite.


## Command

```powershell
wslc run --rm --name codex-wslc-pr8857-xvfb-a17-20261013 --pull never --network none --cpus 1 --memory 512M --user 65534:65534 --env PYTHONDONTWRITEBYTECODE=1 --volume "<study>/INPUT:/src:ro" --volume "<study>/results/a17-01:/out:rw" --workdir /src/research/doom sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592 python experiment_candidate.py
```

The only candidate attempt is `a17-01`; any setup/runtime failure is retained and not retried. Preflight `codex-wslc-pr8857-preflight-a17-20261012` tested the same source-read-only and UID-65534 writable output mount behavior in a separate disposable container; it is not a candidate attempt.
