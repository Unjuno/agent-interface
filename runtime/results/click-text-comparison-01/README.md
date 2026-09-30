# Explicit post-click delay through the public MCP tool

A new scripted integration allocation compared the existing public recipe with
and without an explicit 50 ms `wait_update` after mouse release. No backend or
sensor behavior changed. This does not rerun the frozen #4036/#4053 study.

| Explicit post-click wait | Correct saved text | Missing first h | Median tool return |
| --- | ---: | ---: | ---: |
| none | 2/6 | 4/6 | 314.879 ms |
| 50 ms | 6/6 | 0/6 | 369.266 ms |

The payload was `http://m_n`. All four failures saved `ttp://m_n`.
Their existing passive event journals route the first `h` to the root widget,
then record the Entry click and subsequent `t`. The eight successful cases
record `h` on the Entry. All twelve operation receipts say `completed`:
execution completion did not establish task success.

## Conditions and decision

Current main `853af8b6d432ef5a5242c0d4d571e8a140875822`, Ubuntu WSL,
one private Xvfb/Openbox display, JP keyboard map, twelve fresh ordinary Tk apps.
The schedule `[0,50,50,0] * 3`, payload, source hashes and no-retry rule were written
before any case. Programs differ only in identity/lease time and the optional
post-click delay. Both arms retain 20 ms between characters and a 100 ms wait
after save, totaling requested waits of 280 or 330 ms. Each case sends 29 native
events and uses three public MCP tool calls (observe, dispatch, close), with no
repair or additional observation. Saved-file equality is checked after close.

**Integrate the explicit delay as a scoped example, not an automatic default.**
It helped this fixture in these six cases, at roughly 54.4 ms higher median tool
return. This is a small balanced construction comparison, not a natural failure
rate, statistical reliability claim, minimum safe delay or guarantee for other
apps. Delays cannot prevent later focus changes. Keep value review before a
consequential submit and author repairs explicitly when needed.

This invokes the actual public `server.call_tool` argument validation,
admission, persistent X11 execution, capture and presentation paths in-process.
No provider/model or stdio relay participates. Tool return is measured locally
around `interface_dispatch`; it is not first useful model feedback, semantic
completion, total user task latency, tokens or cost. The model chose the fixed
comparison program but did not inspect images to select each case's actions.
Coordinates are scripted fixture geometry, not semantic target acquisition.

## Evidence and cleanup

`raw.tar.gz` retains all requests/replies, captures, raw reports, programs,
effect files, passive events, per-case results, pre-run plan, environment,
runner and process outcomes. Original failures are unchanged. No retries were
made. All MCP sessions closed with verified releases. All tracked processes
are terminal: fixtures were intentionally terminated with SIGTERM (-15), Xvfb
returned 0, and Openbox returned 1 during teardown. These actual statuses are
retained; cleanup is not described as all-zero. Xlib emitted missing-xauthority
diagnostics; no claim of an authenticated-display replication is made.

Run `python3 -O runtime/results/click-text-comparison-01/verify.py` for a read-only
check of archive integrity, exact schedule and programs, independent saved
values, event recipients, receipt completion/releases, closure and derived
metrics. It does not run the GUI or establish a general causal guarantee.
