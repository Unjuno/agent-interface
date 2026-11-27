# R01 — public Win32 MCP Calculator observation

**Disposition: `HOLD_BEFORE_INPUT`.** The standard public MCP server returned
an observation for the configured Calculator HWND and a consistent target
generation, but the retained `window_client` image is uniformly black: all
170,560 pixels are RGB `(0, 0, 0)`. The predeclared visual gate therefore
stopped the run before validation or dispatch. No task input was sent.

The server closed with zero input calls and zero unresolved calls. Its
`interface_close.release_confirmed=false` means close performed no release;
there was no input to release. Task success and action release are not
applicable. The raw runner's generic stop text says the operator did not
authorize dispatch; [`DECISION.json`](DECISION.json) records that the actual
reason was the black observation without changing the raw result.

This was an integrated-entry observation failure on one native Windows app.
The Win32 backend's `window_client` implementation uses GDI `PrintWindow` with
`PW_CLIENTONLY`, but this run does not establish why the returned pixels were
black. The additive audit passed 12/12 checks. A prelaunch hash-check helper
initially resolved one source path incorrectly; it was repaired before the
server was started, and frozen source hashes then passed.

The next discriminator is a new, input-free `screen_physical_px` observation
through the same public server. It can determine whether desktop capture sees
the visible app while window capture does not. R01 remains immutable and is
not retried. This result says nothing about model tokens, efficiency,
reliability, MAP01, blocked-I/O release, or WSLc.
