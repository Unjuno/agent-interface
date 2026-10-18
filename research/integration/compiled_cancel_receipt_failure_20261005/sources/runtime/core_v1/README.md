# Agent Interface runtime core v1

This directory is the first promoted, platform-neutral runtime contract. It does
**not** implement native GUI control by itself.

Promoted semantic boundary:

- explicit backend capabilities: `supported`, `unsupported`, `unknown`, `permission_required`;
- explicit Linux / Windows / macOS platform identity without inferring support;
- observation sequence and binding-revision freshness;
- finite authority lease expiry;
- coordinate-frame compatibility;
- fail-closed capability admission;
- exactly one terminal `release_all` operation.

The universal office-control floor remains capture, keyboard, text, pointer,
scroll, focus, display geometry, monotonic clock, feedback and release-all.
Clipboard, accessibility and window enumeration are optional accelerators rather
than correctness prerequisites.

## Why this is promoted

The contract is derived from retained research evidence:

- `portable-runtime-v01-20260915-01`: 27/27 deterministic tests and 1,000 valid
  program round-trips;
- `native-core-go-v0-20260915-01`: 12/12 tests, 10,000-program deterministic
  stress and 5/5 cross-builds;
- `x11-backend-conformance-20260915-01`: private Xvfb/XTEST/Xlib backend
  mechanics with 64/64 seeded release/effect cases.

Those results justify promoting the semantic/backend boundary. They do **not**
justify claiming native Windows, macOS, Wayland or general Linux GUI support.

## Backend rule

A native backend implements `backend.Backend`, publishes a validated manifest,
and receives only programs that pass `contract.admit_program`. A platform probe
is discovery evidence only; it grants no input authority.

Run offline tests:

```bash
python -m unittest discover -s runtime/core_v1 -p 'test_*.py' -v
python -m runtime.core_v1.doctor
```
