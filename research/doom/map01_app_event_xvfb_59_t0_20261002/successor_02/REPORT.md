# Issue #59 T0-02 — X11 server occupancy versus app event delivery

## H / T / D / C / U

- **H:** `XQueryKeymap` is server-global state, not proof that the currently
  focused application received a corresponding `KeyPress`.
- **T:** Under private Xvfb, an app window A received W down/up in a
  stable-focus positive control. In the contrast, W was pressed with A focused,
  focus moved to B while W remained down, then W was released. The candidate
  captured seven complete 32-byte keymap samples and the client event stream.
- **D:** `PASS_X11_APP_DELIVERY_BOUNDARY_SCOPED` if the positive control
  delivered both events to A, then the server keymap stayed down after B became
  focused while B received no W `KeyPress`; all source identities and server
  cleanup had to verify.
- **C:** Frozen source main `2b25814229e6b7072a7e28eeaa8870f4448354ae`.
  Predecessor T3 tested per-occurrence keymap witnesses only. T0-01 stopped
  before Xvfb startup at candidate image identity preflight and remains
  unchanged. T0-02 is a new frozen allocation with the image pinned from host
  inspection and a Python entrypoint override; it is not a retry of T0-01.
- **U:** Private Xvfb + synthetic XTEST only. This establishes neither physical
  keyboard occupancy nor semantic/useful application effect, game input,
  held duration, authority, MAP01 threat response, survival/progress, safety,
  latency, or product efficacy. Image is `linux/amd64` under OrbStack on an
  arm64 host (emulated); timing is not generalized.

## Formal result

Allocation `ISSUE59-X11-APP-DELIVERY-T0-20261002-02` ran candidate once and
independent raw-only auditor once; retries 0.

- Stable-focus positive control: A received W `KeyPress` and `KeyRelease`; the
  server-global W bit was false → true → false.
- Focus-transfer contrast: A received W `KeyPress`; after focus moved to B the
  global W bit remained true, while B received **zero W `KeyPress` events**.
  Upon release, B received W `KeyRelease` without a preceding W `KeyPress` in
  that window's recorded interval.
- Xvfb exited 0; its socket and lock were removed. The independent audit found
  zero errors and rejected all 5/5 evidence mutations.

Disposition: `PASS_X11_APP_DELIVERY_BOUNDARY_SCOPED`. This directly validates
the observability boundary that Issue #59's held-input/effect accounting must
not collapse: a server keymap witness and the focused application's event
receipt are distinct evidence. It does not satisfy #59's required live
threat-exposure or MAP01 gate.

## Execution and audit

Image: `map01-attack-onset-phase-a2:20260927-r2`,
`sha256:fc3022d265f465748e0a39491e28f8447d0066266e00d2a8a9144e866bf148ed6`.
The formal containers used `--pull=never`, `--platform linux/amd64`, network
disabled, 1 CPU, 768 MiB, 96 PIDs, read-only root, `no-new-privileges`, and a
96 MiB noexec/nosuid `/tmp` tmpfs. The inherited desktop entrypoint was
overridden, so no extra Xvfb/Openbox pair was started. The source bind mount was
read-only; only `results/formal-02/` was writable. The preformal Docker
construction suite passed 5/5, and a private-Xvfb startup/cleanup preflight
passed before the frozen candidate invocation.

Raw SHA-256:
`d7ee4094e98294c46ae35a56e361c5cb66afc69f3fa9575f7ef5997a5914d8df`.
Independent audit SHA-256:
`448ebee85c9cf0ec0c84757a83b512310a095e1fac4c641ea103f5ab663803f6`.
Full action/event rows, keymap bitmaps, run commands, identities, and
predecessor STOP are retained alongside this report.
