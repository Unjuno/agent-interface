# Issue #706: retained release-versus-abort boundary and failed control

**Disposition: STOPPED_CONTROL_FAILURE. Frozen auditor: FAIL_INTEGRITY_OR_CONTROL.**

This allocation ran in the disposable container, not GitHub Actions. It instantiated 10 of 12 frozen first cases and stopped on the first control failure. There were no formal reruns, replacements, extensions or source/threshold changes. The final two cases remain unstarted. This is evidence retention, not runtime promotion or a full-block PASS.

## First outcomes

| Scenario | Planned | Recorded first cases | Button commands | Frozen case checks |
| --- | ---: | ---: | --- | --- |
| cancel before begin | 3 | 3 | zero in all three | 3 pass |
| normal completion | 3 | 2 | one in both | 1 pass; 1 expired-end control failure |
| cancel after begin | 3 | 3 | one in all three | 3 pass |
| expiry after begin | 3 | 2 | one in both | 2 pass |

All 10 cases ended with server button/key state and logical touch state neutral. All 20 owned child processes were reaped. All 8 non-normal cases rejected their post-terminal continuation without additional touch input. The receiver's stock Tk Button class binding was not replaced. Raw press/release/command events and separately read before/pressed/after PNG pixels agree.

**Scoped observation:** all five measured post-begin cancellation/expiry cases invoked one Button command after release, even though input ended neutral. Cancel-before-begin controls3/3 emitted neither input nor effect. This is counterexample evidence against equating neutral release with semantic abort. It is NOT completion of the preregistered six post-begin observations and does not invalidate #655's contact-lifecycle result.

## Why the allocation stopped

`m09-complete-r1` requested its ordinary end at 511.412447 ms after authority start under a 350 ms horizon. The unchanged inherited Authority.task released the contact, then returned `{accepted:false, reason:EXPIRED}`. Release dispatch occurred 161.455982 ms later than the deadline. The stock Button still executed once. This normal-completion case failed its frozen control and is not relabelled as an expiry-arm sample.

The preceding normal control requested end at 315.872513 ms and was accepted. One cancellation case requested cancel at 528.127322 ms; this is also retained. The authority is cooperatively serviced, not an independent hard-deadline watchdog. Capture/PNG encoding, X11 queries and scheduling were not separately timed; no unique cause of the delay is asserted.

Unstarted: `m10-expiry_after_begin-r1`, `m11-complete-r2`.

Exact unchanged block audit:

```json
{"decision":"FAIL_INTEGRITY_OR_CONTROL","cases":10,"errors":["case_inventory","m09-complete-r1:normal_completion"]}
```

## Verification and reproducibility

A posthoc checker, importing neither runner nor frozen auditor, verified 267 evidence checks over the stopped prefix with zero diagnostic errors. Its label is VALID_RETAINED_FAILED_PREFIX, not scientific PASS. All six frozen source hashes and the original FREEZE.json remain unchanged. Eight inherited class/function bodies are byte-identical to #655. Six copied-evidence corruption controls are rejected, including wrong effect pixels with an updated image hash.

The eight `formal-replay.part00.bin` through `part07.bin` files reconstruct a 32,680-byte XZ archive, SHA-256 `36341fd243267095c3243f6d19597d38227948549fabef36e3d4052f0796c143`. It contains 131 manifest-bound files plus the manifest: exact frozen source/plan/auditor, all 10 raw result/receiver/state records, all 30 formal PNGs, supervision/STOP, audit histories and posthoc diagnostic/control code. Every part's returned Git blob hash matched its local bytes before this result commit.

A fresh extraction verifies all131 manifest entries. The frozen FAILED audit and posthoc diagnostic both reproduce byte-for-byte, without starting an X server or emitting input. Python3.12+ and Pillow are required for this offline check:

```sh
python reproduce_retained.py --out /tmp/xi2-706-retained-check
```

The output directory must not already exist. A successful reconstruction still reports experiment_disposition=STOPPED_CONTROL_FAILURE.

Bulk Xorg logs and excluded construction/partial-construction files are retained in the conversation's full archive, not claimed to be in the compact GitHub replay. The original source-first commit is `9c4b2219f2fe23d0f8e0c17e3c4a16f444ed52fa`; publication base is `d84027ebd94a786b2143e25e52fe1504deb85ee7`. An initial truncated source upload was rejected by hash before measurement and never referenced by this branch; the original bytes were published in seven verified source chunks instead.

## Scope and design implication

CPython3.13.5 / Linux6.18.44 / Xeon Platinum8370C / Xorg1.21.1.16 / Tk8.6.16, private inputtest DirectTouch, 1024x768/depth24/BGRX. Serial fresh Xorg/Tk cases; frequency and host load unpinned. One contact through native X11 pointer emulation, not physical HID. No model, game, user documents, shared runtime or workflow changes. No population-reliability, performance, cross-platform or universal rollback claim.

Inference: terminal receipts should distinguish input neutrality, admission/authority and observed application effect. A release-only lowering must not advertise abort-without-effect from release verification alone. Mandatory release must still occur. Relevant disciplines are HCI release/commit semantics, real-time deadline enforcement and compiler/capability contracts.

Next single question: can a release-only route be refused before first press when an instruction requires cancellation without application effect, while remaining admissible for instructions requiring only neutral release?
