# X11 uncertain press: preserve release obligations

Research intake (#59/current r133, #4389) distinguishes actual input occupancy,
readback, recovery and useful task effects. The public X11 path had a concrete
recovery gap: it registered a pressed key/button only after its synchronization
returned. A request could already have reached the server when that call failed.

## Reproduced failure

On base `43a8f58c126a8d54cb84f2f4fcd2299b9028b380`, a private Xvfb allocation
processed W-down, then the construction wrapper raised after the actual sync.
The program stopped, but release_all had no tracked key to release or check and
returned `verified=true`. A separate X11 connection then observed **W still down**.
The fixture explicitly released it afterward and independently confirmed up.
No user desktop was involved. This was an injected boundary fault, not a naturally
occurring network failure or a measurement of its frequency.

The first setup attempt used the constructor incorrectly and stopped before
opening the backend or sending input; its script and fixture cleanup are retained.
The distinct successful reproduction is `x11-uncertain-press-before-02`.

## Change

Code `366a3ce849f62d48ce990c3cf9227867d94ad101` records cleanup obligations before
attempting key/button presses. A failed send or sync therefore leaves enough
information to attempt release. Explicit key/button up removes the obligation
after successful synchronization. release_all now preserves obligations when
readback raises, and retains inputs that readback still reports down. A later
explicit recovery can release them; there is no automatic replay of the failed
application action. Successful paths add no X11 request or wait.

## Verification

- Four fresh private X11 controls: keyboard/button, failure after send processing
  or after sync processing. Each stopped at operation 0, skipped the following
  wait, attempted release, and a separate connection observed W/left-button up
  before final fixture cleanup. All owned Xvfb/Openbox children exited.
- Unit controls cover those four boundary combinations, failed readback retaining
  obligations, and down readback retaining only outstanding inputs for a later
  explicit recovery. Full local suites: **267 protocol + 121 harness** passed.
- The exact portable runtime was imported by a real stdio MCP server with one
  documented fault-injection wrapper. First dispatch returned execution_failed
  and verified release; independent readback occurred before any next action or
  close. A separate explicit 20 ms hold/release program then completed on the
  same session, and a second independent readback confirmed up. Explicit close
  succeeded and the SDK context exited normally. This was programmatic boundary
  validation, with no model or GUI task policy.
- The first MCP construction stopped at the client import because that venv lacked
  numpy. Its STOP note is a retrospective setup record, not a captured traceback.
  The fresh `-02` construction uses the existing system package directory for
  the parent fixture only; no dependency was installed or runtime archive edited.

Portable SHA256:
`4950a1d2ec4e530b9df9ac74e37e991765471b95c89bd9ee02977a8a91b01f97`.

## Scope

Separate-connection readback is a state sample, not exact physical edge timing,
continuous occupancy, application receipt, useful feedback or task effect. It
does not close those research gates or prove human tempo. No sensor service or
helper model is introduced. An inaccessible server/connection can still prevent
release/readback; process kill and host failure remain outside this guarantee.
Recorded emission counts cannot count requests whose send call raised after
possibly emitting; the retained failed-op effect remains explicitly uncertain.

Raw evidence preserves setup failures, before/after outcomes, sources, scripts,
runtime/build identity and test logs. Verify without executing archived code:

```sh
python3 -O runtime/results/x11-uncertain-press-release-01/verify.py
```
