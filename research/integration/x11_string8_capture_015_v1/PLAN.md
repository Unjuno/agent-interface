# XGetImage String8 behavior on Python-Xlib 0.15

Issue: #4638, successor to unresolved compatibility question #4455. Preserve #4304's STOP, #4455's 0.33 HOLD, and PR #4611 unchanged. Local source is derived from the tested #4455 harness; this allocation is version-specific and not pooled with it.

## H — hypothesis

On the frozen local Linux/amd64 Docker environment using Python-Xlib exactly 0.15, at least one legal XGetImage String8 payload is exposed as str, causing the legacy bytes(image.data) conversion to raise TypeError. UTF-8 re-encoding will reconstruct exact native XGetImage bytes; existing bytes payloads remain byte-identical.

## T — formal treatment

- Base: official cached python:3.11-slim@sha256:da047cb8f9d1d98e5c070f5300ba9f7274e33b8fc0e5be5ed88740aed1b95ba9 (Linux/amd64, Python 3.11.16). The Dockerfile installs Xvfb, xauth, libX11, and the official PyPI distribution python3-xlib 0.15 inside the image. The current python-xlib distribution begins at 0.16; the historical 0.15 package name is python3-xlib. Record actual apt package versions, package-artifact hashes, Docker image ID/digest, and Python/library versions in ENVIRONMENT.json. No host package/environment mutation.
- Each excluded construction/formal case has a fresh private authenticated TCP-disabled Xvfb and fixture process. The fixture paints deterministic 8x8 patterns to the root or a child drawable. A separate libX11 connection captures the native XGetImage bytes and pixels as the oracle.
- Five frozen patterns (all-zero, low ASCII plus valid multibyte UTF-8, invalid high byte, mixed, ordinary color) × two targets × three repetitions = 30 cases. Enumeration is deterministic in SCHEDULE.json; there is no random shuffle/seed.
- Retain response type/text-or-bytes, legacy conversion result, UTF-8 candidate bytes, native oracle bytes/pixels, geometry/depth/stride, hashes, process IDs/exits, display isolation, and cleanup. No model/provider, task input, user desktop/data, or runtime import. Formal container uses --network none, read-only root, and only a bounded tmpfs plus evidence output mount.
- The sole candidate expression remains image.data.encode("UTF-8") if isinstance(image.data, str) else bytes(image.data). It is measured only; this allocation does not patch shared runtime code.

Construction is excluded from formal. The prior 0.33 harness tests are a setup check only. Record every setup/build/test failure and correction. Publish/read back exact source, Docker recipe, source manifest, environment, schedule, auditor, and decision gates before the first formal case.

## D — frozen gates

PASS_X11_STRING8_PY015_BOUNDARY_SCOPED requires all 30 rows and process receipts to reconcile; at least one live str causes the exact legacy TypeError; candidate bytes equal native bytes for every row; bytes inputs are identity-preserved; no length/hash/pixel-oracle mismatch; all owned processes exit and cleanup is complete; independent raw-only audit errors=[]; and all 12 copied-evidence corruption controls reject.

HOLD_NO_LIVE_STRING8_DISCRIMINATOR_PY015 if the complete audited matrix contains no str/legacy TypeError. A complete native-byte or pixel-oracle mismatch is FAIL_STRING8_INVERSION_PY015. Missing or inconsistent source, environment, row denominator, raw evidence, process receipt, audit, or controls is typed HOLD/STOP. Formal invocations=1; retries/replacements/exclusions/tuning=0.

## C / U

This is a representation-boundary experiment on one locally built Linux/amd64 image and synthetic Xvfb drawables. It does not establish pixel-channel/endian interpretation beyond the independent fixture oracle, application semantics/freshness/effects, local-model quality or utility, latency/tokens, prevalence, other Python-Xlib versions, cross-platform behavior, or production reliability. No outcome here alone authorizes a runtime patch.
