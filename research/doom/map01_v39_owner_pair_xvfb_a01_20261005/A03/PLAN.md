# A03 plan: align Xvfb startup and readiness display

Issue #59; a separately frozen successor to A02 STOP, not an A02 retry.

## H / T / D / C / U

- **H:** With the Python-Xlib list-to-bytes normalization and a runner that
  starts and polls the same Xvfb display, the one-owner control and two-owner
  shared-display scenario will expose a server-global keymap release while a
  peer owner still has W in local bookkeeping.
- **T:** One candidate invocation on private display `:97`, using the exact
  PR #7974 head frozen in A03/FREEZE.json. First run one-owner W down/up, then
  two independent V4/V3/V12 owners with distinct leases and W on the same
  Xvfb server. A third Xlib client samples keymap. A02's only execution change
  is corrected Xvfb display-number consistency across launch, socket check,
  readiness polling, candidate DISPLAY, and output schema/path.
- **D:** Apply the frozen shared-display rule: control server keymap
  false/true/false; pair false/true/true/false/false; distinct owners/leases;
  A up is server-keymap verified while B locally still owns the key; B up is
  verified; final server keymap is neutral; cleanup errors empty. Preserve any
  setup STOP or complete-run mismatch without retry. Confirmation is a
  shared-display isolation failure only.
- **C:** A01 stopped before key injection because of candidate-side Xlib type
  handling. A02 stopped before candidate start because runner launched `:98`
  but polled the `:99` socket. A03 repairs only that runner mismatch and uses
  a fresh experiment/output ID; those predecessor results remain unchanged.
- **U:** This is a single private Xvfb observation of server keymap and local
  owner bookkeeping. It does not establish physical state, app/game receipt,
  production display exclusivity, threat control, useful feedback, recovery,
  or MAP01 outcome.
