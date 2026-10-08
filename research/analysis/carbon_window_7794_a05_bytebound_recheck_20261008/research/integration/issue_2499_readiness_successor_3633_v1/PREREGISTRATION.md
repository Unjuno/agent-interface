# Issue #3633 — readiness identity v4 formal-01 preregistration

Allocation ID: `issue3633-readiness-identity-v4-formal-01`.

## Hypothesis

The v4 filtered X11 resolver plus the repository's typed three-app readiness
gate will identify one stable Inkscape, LibreOffice Calc, and Chromium main
surface on one private display. The gate will refuse missing, ambiguous,
unstable, duplicate, malformed, or wrong-display identities. No geometry,
focus, transition, or input operation is needed for this prerequisite.

## Frozen procedure

1. Run the repository `mixed_app_identity_2666.test_identity_gate` suite in
   the pinned local Linux/arm64 image.
2. Start private Xvfb `:141` with a private Xauthority file and isolated
   per-app profiles. Launch Inkscape, LibreOffice Calc, then Chromium.
3. Retain complete visible-window title, PID, WM_CLASS, display and probe
   return-code records after each launch. Take two full consecutive snapshots
   after all three apps have launched.
4. Apply frozen filters: Inkscape title/WM_CLASS contains `inkscape`;
   LibreOffice Calc title/WM_CLASS contains `libreoffice calc`; Chromium
   title/WM_CLASS contains `chromium`. Each must yield exactly one candidate
   in each snapshot. Apply `evaluate_identities` from the frozen main source
   to both selected maps. Require exact stable records and distinct `(window,
   PID)` pairs.
5. Terminate process groups and Xvfb, retain exit/reaping and X-socket state.
   No geometry/focus/input/model/network calls. Run `audit.py` in a new
   network-disabled container with source and raw result mounted read-only;
   write only the independent audit output.

## Outcomes

- `PASS_READINESS_IDENTITY_V4_SCOPED`: all three live identities admitted;
  the 4 negative contract tests pass; forbidden operation counts remain zero;
  cleanup and independent audit pass.
- `STOP_READINESS_IDENTITY_UNAVAILABLE`: a bounded app startup/identity query
  is missing or ambiguous, or the readiness gate refuses before any forbidden
  operation. An auditor may verify this STOP classification; it is not a
  scientific PASS or a FAIL of the long-session hypothesis.
- `FAIL_READINESS_IDENTITY_V4`: malformed/ambiguous identity is admitted, any
  forbidden operation occurs, cleanup is not neutral, or the independent
  audit contradicts retained evidence.

No retries or source/threshold/filter changes after formal invocation begins.
No full-session experiment is part of this allocation.

## Construction-only observation (excluded from formal result)

Before freeze, the image's existing discovery entrypoint was run once as a
construction check. It reported visible Inkscape (`2097159`, PID 9), Calc main
(`6292261`, PID 61), Calc Tip-of-the-Day auxiliary (`6292535`, PID 61), and
Chromium (`4194307`, PID 68); first/second observations were stable and all
apps were alive. No input, model, network, geometry, or focus operation was
performed. The frozen Calc filter intentionally requires `LibreOffice Calc`
in the title, excluding the auxiliary Tip-of-the-Day window whose title lacks
that string. This observation is not counted as a formal row.
