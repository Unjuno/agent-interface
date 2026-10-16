# Private X11 readiness and Operations World primary smoke

The shared `PrivateSession` fixture now checks that Openbox has made a disposable
window both viewable and present in `_NET_CLIENT_LIST` before launching an app.
It retries only that probe's map request every 200 ms, checks process exit and a
3-second deadline, then destroys the probe. Failure closes the fixture's owned
processes. Xlib calls remain synchronous: this is not a hard wall-clock watchdog.
No application input is retried, and no runtime wait or input contract changes.

## Why

On Ubuntu/WSL with private Xvfb/Openbox, Operations World remained alive but its
window stayed unmapped. Restarting WSL did not resolve it. A successful X11
handshake and the inherited 200 ms startup sleep were insufficient in this
environment. Retained diagnostics distinguish:

- original startup timeout and subsequent unmapped observations;
- post-restart reproduction, and a connection-sync-only check that still failed;
- a second small window allowing mapping to proceed;
- a 1-second app-launch delay allowing mapping;
- a one-shot readiness probe failing one of three fresh sessions;
- a repeated probe map request allowing all three sessions to proceed.

This localizes an observable startup-order dependency. It does not establish the
exact internal Openbox/Xlib cause or universal reproduction frequency.

## Integrated check

Code commit: `137617ce4`. Base: `442ef765598971806dc5d671a223af7b3a711a5f`.
Three fresh sessions using the integrated helper all listed Operations World.
Probe readiness took 216.164, 214.591 and 216.349 ms; app listing after spawn took
22.795, 17.034 and 19.089 ms. These are setup measurements, not model-feedback
latency or performance improvements. Stopped and exited window-manager controls
were refused; no probe remained. All owned processes were reaped.

Local native checks: **262 protocol + 118 harness tests passed**. The real-X11
check script, outputs, screenshot, changed sources and pre-change fixture source
are retained in `raw.tar.gz`, along with the unsuccessful diagnostic allocations.
Inspect scripts before using them: their output paths are deliberately exclusive
and must be changed for any fresh experiment. The verifier never executes them.

## Primary-operated public MCP smoke

`ops-world-primary-02` used the previously built public runtime from base commit
442ef7655, persistent-X11 mode, known seed 42/family 99173 and real-time stepping.
Watchers/alerts/events were explicitly disabled for this construction check.
There was no helper model or hidden evaluation. The evaluator report was read
only after normal application exit.

Six actual tool calls are retained:

1. Observe: visible first-person scene, but HUD text absent.
2. Forward program refused before input: embedded `observe` requires `x/y/w/h`,
   whereas the public observation tool accepts a `region` array. Zero emissions.
3. Corrected new program: hold W for 500 ms, release, observe; visible perspective
   changed and release verified empty.
4. Pointer move, 100 ms wait and observe: visible scene orientation changed;
   release verified empty.
5. Alt+F4: application exited normally with code 0; release verified empty.
6. Explicit session close: verified empty release; relay exited 0.

Primary review notes are bound to retained reply hashes. They are attribution,
not independent proof of understanding. The terminal report records **success
false**, no completed work tasks, and roughly 123.95 seconds of both wall and
simulation time. This is motor/feedback usability evidence, not task completion,
human-tempo performance, a speedup or token/cost savings. Public caller-asserted
observation/lease authority and fixed-delay semantics are unchanged.

## Post-run interpretation and next integration work

The primary initially found the lack of HUD text confusing; those review notes
remain unchanged. Post-run source inspection shows that `render_task_cues` draws
shape/color cues, while text is used inside source/terminal panels and at session
end. `VALIDITY_HARDENING.md` explicitly removes cumulative progress counters from
the visible surface. With watchers disabled, an empty top strip is therefore not
evidence of a rendering defect. Task discoverability needs a separate real-use
check that preserves evaluator isolation; do not restore private progress data
merely to make this smoke easier. The mismatched observation argument shapes are
a directly experienced authoring cost: consider a shared documented recipe or
explicit conversion rather than silently accepting malformed core programs.
Neither usability question is resolved by this startup change. DOOM remains one domain among
several, not the architecture's sole target.

Verify retained bytes and scoped outcomes with:

```sh
python3 -O research/live_control/results/private-x11-readiness-01/verify.py
```
