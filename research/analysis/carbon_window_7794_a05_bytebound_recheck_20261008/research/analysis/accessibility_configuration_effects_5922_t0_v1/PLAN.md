# Issue #5922 T0 — accessibility-configuration effect invariance

Status before freeze: construction only. No formal candidate/auditor invocation has occurred.

## H / T / D / C / U

- **H:** A route that succeeds with default presentation may silently miss or mis-target an operation after accessibility-related presentation changes. A fresh semantic rebind should preserve a verified task effect when equivalent functionality/evidence remains; stale/unavailable evidence must return typed UNKNOWN and never be promoted to success.
- **T:** Eight deterministic synthetic interface states × three frozen routes (`raw_coordinate`, `fresh_semantic_rebind`, `explicit_unknown`) = 24 records. Cases cover default, benign 200%-text reflow, a destructive decoy at a cached coordinate, high-contrast color inversion, reduced motion with a static status, reduced motion without status/receipt, an app configuration that removes the operation, and a stale accessibility-tree epoch. An independent oracle compares action target/value, scoped authority, release, and effect receipt.
- **D:** `PASS_METHOD_SCOPED` only if the independent oracle has zero disagreements; fresh semantic rebind never emits a forbidden object/value; the decoy and stale-tree controls are detected; valid presentation-preserving cases retain exact save effects; absent functionality or stale evidence returns UNKNOWN without actuation; missing completion receipt never becomes SAVED; and every emitted discrete action records release. Raw-coordinate faults are measured, not averaged away. The route itself is not claimed to provide accessibility support.
- **C:** Synthetic geometry, colors, accessibility-tree entries, configuration labels and receipts are stipulated rather than rendered/extracted; no human or assistive-technology participant is represented. The fixture can establish only logic under its declared oracle.
- **U:** No actual browser/desktop renderer, WCAG conformance, screen-reader, magnification, user benefit, OS-level setting, broad GUI reliability, production, or model claim. A setting that removes app functionality is an application/configuration limit and must be UNKNOWN, not normalized into agent failure/success.

## Formal protocol

Freeze fixture, candidate, independent auditor, tests and this plan. Read all source blobs back from the source-freeze commit and compare identities. Run candidate exactly once and retain stdout; run independent auditor exactly once and retain stdout. Auditor includes three mutation-only negative controls; they do not rerun the candidate. Any failed formal gate remains immutable; no retry/relabel.

This is a no-external-effect Python fixture. Docker Desktop service/processes are currently present, but the shared Docker inventory is not responsive/verified, no Issue-specific lease is assigned, and another task has a bounded isolated OrbStack slot. Do not start/inspect/touch the shared engine for this fixture; use local host CPU, and record the exception. No extra packages, GUI, network, input, model, GPU or app settings are used.
