# #5156 T3: independently auditable XQueryKeymap witnesses

## Status

Host-only construction is verified; formal X11/Docker execution is **NOT RUN**. This directory is an additive successor and does not alter A06 or any previous raw result/STOP. It is not yet a formal #5156 result and does not claim physical key occupancy, application consumption, or MAP01 effects.

Repository freeze: main `8ee4ff891a54827b3df3df297cdb849e2aea428e`, observed 2026-09-30 UTC. The proposed identity is `MAP01-OWNER-KEYMAP-WITNESS-5156-T3-20261001-01`; it is a unique label only, **not a reservation or permission to run**. Vendored dependencies are copied byte-for-byte from A06's tracked frozen bundle at that main commit; see `SOURCE_MANIFEST.json` for every repository path and SHA-256. In particular, bundled `input_owner_v11.py` is A06's owner-thread implementation and is not the current top-level telemetry wrapper of the same filename. Recheck main and all manifest hashes before formal use. There is deliberately no launch/slot dispatcher here: a fresh exclusive allocation, queue reconciliation, image/platform inspection, and a new one-shot launch contract must be established first. Never reuse an earlier allocation or another lane's slot.

## H / T / D

**H:** Persisting each 32-byte XQueryKeymap bitmap, monotonic observation timestamp, case/stage, and admitted keycode map lets a raw-only auditor independently verify server key-state transitions instead of trusting runner booleans.

**T:** In a future disposable Xvfb fixture, capture pre-down, post-down, and post-terminal snapshots for a single-key explicit release, ordered two-key explicit release, and partial-cancel cleanup. Do not query between the two release requests. Run the candidate once and, only after zero exit, run the raw-only auditor once.

**D:** Host tests require exactly nine unique case/stage witnesses; decode exactly 32 bytes; match keycode maps to the complete expected admission inventory; verify the entire bitmap equals the expected pressed-key state with no unaccounted pressed keys; and verify monotonic timestamps. Held-state samples must precede release requests and terminal-state samples follow the corresponding XSync completion. Two-key snapshots occur only before the first and after the second release. Missing, duplicate, malformed, contradictory, identity-mismatched, or mistimed witnesses fail closed. Fixture allocation/frozen-main identity must match `EXPECTED.json`. The audit result remains server processing/state evidence only.

## C / U

**C:** XQueryKeymap is a server-state snapshot, not a continuous physical-occupancy measure or proof that an application consumed an event. A single X server/fixture does not characterize scheduling variability.

**U:** No live MAP01 occupancy, efficacy, safety rate, recovery quality, human tempo, latency, or cross-domain transfer is established. No MAP01/control interaction is part of this construction.

## Reproduction

From this directory run:

```sh
python3 -B -m unittest -v test_keymap_witness test_audit_formal_x11 test_serialize_release
python3 -B -m py_compile audit_formal_x11.py run_formal_x11.py
```

Latest host-only result: 20/20 tests passed; `py_compile` and `git diff --check` passed. This does not imply Docker/X11 execution. Preserve the exact stdout and file hashes when recording a new run.
