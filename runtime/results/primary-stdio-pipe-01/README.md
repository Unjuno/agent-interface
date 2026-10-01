# Corrected raw-file primary stdio connection

Source is pinned in manifest.json (34fe70678, including TTY refusal and output
error preservation). One fresh no-GUI connection, after the earlier terminal
owner was confirmed ended. The primary actually sent one numbered clock command
through the persistent tool terminal handle with CLI stdout redirected to a fresh
owned file under shell noclobber. Raw output remained valid JSON-lines with no
ANSI rendering artifacts. The primary read its original execution-clock reply,
then sent EOF; the same transport and owning process exited 0.

This is a new corrected-source transport probe, not replacement/replay of the
first terminal trial. The initial TTY-rendered output and failed public-close
request remain in primary-stdio-terminal-01. This nonpersistent public MCP probe
uses only interface_clock: it invokes no backend, native input, capture, or app.
No public close is claimed; that tool is unavailable under this configuration.
Real guarded-x11 self-use requires its own owned display/window and evidence.

No per-command input JSON files or custom primary host-dispatch script were
authored. One initial configuration file and raw stdout file remain, along with
the unchanged exchange/host evidence writes. Outer image delivery, parsing,
review and owned app/process lifecycle are still the caller's responsibility.
This is not current-thread MCP registration or a general route/cost/tempo benefit.

Corrected-source local tests: nine focused stream/owner tests, 180 total Node
relay/host tests, nine committed-source distribution tests. The first red import
failure and pre-guard tests are retained separately with the initial terminal
record. verify.py checks full raw stream/file/original metadata identity, exact
one clock, no image/input, terminal original transport, archive and all committed
host bytes. Normal and -O results are retained. No actual provider cost or model
token savings were measured for this component probe.
