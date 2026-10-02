# Issue #6684 T0 — preregistration

Status: pre-freeze construction. This is a finite authored method comparison, not a GUI/live-action evaluation.

## H / T / D / C / U

- **H:** A DBM-style relational abstraction strictly reduces `UNKNOWN` relative to independent coordinate boxes in frozen common-frame translation cases, with zero false admissions against exhaustive concrete enumeration. Under independent target/action frame shifts it must show no gain.
- **T:** Enumerate integer x/y shifts and calibration errors for one immutable target and one adjacent forbidden object. Compare independent interval hulls (BOX), a difference-bound matrix (DBM), and exact state enumeration (EXACT-JOINT). Preserve concrete states, bounds, decisions, reasons, and counterexamples. Test relation sign, units, frame, epoch, identity and contradictory-bound mutations. No model, GUI, network, user data or OS input.
- **D:** PASS_METHOD_SCOPED only if an independently implemented raw-only auditor verifies every concrete state and bound, DBM admits every frozen all-safe common-mode case refused by BOX, gains nothing over BOX in the independent-shift control, and every invalid mutation refuses. False admission => FAIL_UNSOUND; no common-mode gain or unexpected independent gain => FAIL_NO_GAIN; audit mismatch => HOLD_AUDIT.
- **C:** The finite fixture may be equally precise and simpler; authored relations may encode only this fixture; conservative boxes may be adequate for actual GUI targets.
- **U:** Integer translation geometry excludes scaling, rotation, rendering, DPI, occlusion, changing hitboxes, semantic identity, focus, input delivery and application effects. No GUI safety or runtime benefit follows.

## Frozen construction

Units are integer pixels. Target center `(10,10)`, inclusive half-width 2; forbidden neighbor center `(14,10)`, half-width 1. Common-mode cases share a bounded translation across target, action and neighbor; action calibration error varies independently. The independent control separates action from target translations. DBM projects `action-target` and `action-forbidden`; BOX takes independent absolute-coordinate interval hulls before subtraction; EXACT-JOINT enumerates all assignments and is safe only if all hit the intended target and avoid the forbidden object.

Construction and adversarial audit tests must pass before freeze. Then hash all source/configuration, execute candidate once in a fresh WSLc session with networking disabled, one CPU, requested small memory limit (not presumed enforced), read-only inputs and a dedicated writable output. Run the separate auditor once read-only against raw output and truth. No retries or host-as-formal substitutions. If WSLc denies before execution, record STOP/INFRA and do not rerun this allocation.
