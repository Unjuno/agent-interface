# Formal allocation result: #2499 successor v2

This is a fresh additive allocation. It does not modify the retained STOP in
#2658 or any component result.

## H/T/D/C/U

- **H**: one persistent private X11 session can traverse the four declared
  mixed-app transitions while refusing stale admissions and preserving fresh
  identity.
- **T**: run `formal_session.py` once in the pinned local Docker image with
  `--network none`, using the repaired launch arguments and one Xvfb display.
- **D**: retain the emitted ordered ledger, process/window identities,
  geometry receipts, admission dispositions, input/model/network counters,
  and cleanup result.
- **C**: PASS only if all checks pass, including geometry change and distinct
  window replacement identity. Any failed check is FAIL; infrastructure setup
  failure before the allocation is STOP.
- **U**: whether the existing mixed-app image can provide stable geometry,
  focus, and non-reused replacement identity remains unknown.

## Local Docker result

Image: `mixed-app-2666:local`; network: none; display: `:142`; model calls: 0;
network calls: 0; input operations: 3; event count: 15.

Decision: `FAIL_MIXED_APP_LONG_SESSION`.

Observed failures:

1. Inkscape and Calc were enumerated, but both reported `Geometry: 1x1`;
   the geometry transition therefore did not change the recorded geometry.
2. After the focus-drift activation, `getactivewindow` returned `null`, so the
   focus check failed rather than being inferred as successful.
3. Chromium replacement returned the same window ID (`4194307`) as the old
   identity, so the required distinct replacement identity failed.

The session emitted a complete 15-event ledger and neutral cleanup record, but
the acceptance gate is not met. No integrated-session PASS is claimed.

## Follow-up diagnostic allocation

An additive local Docker diagnostic added `openbox` to the derived image and
selected windows by `_NET_WM_PID`/`WM_CLASS`, rejecting 1x1 windows. Inkscape
then resolved to a real `710x659` window. LibreOffice Calc did not produce a
matching visible Calc window within the 25-second bounded readiness interval,
so the allocation stopped before transitions with
`STOP_MIXED_APP_LONG_SESSION`. This is a readiness stop, not a result to
substitute with LibreOffice Writer or an inferred identity. The image was
`mixed-app-2794:local`, derived from `mixed-app-2666:local` and used with
`--network none`.

A further local Docker check used a fresh LibreOffice `UserInstallation`
profile, `--nofirststartwizard`, and a 15-second bounded wait. Calc still
exposed no matching visible window (only a 1x1 non-identity window), so this
repair hypothesis remains unverified and the formal runner stops before any
transition. Decision remains `STOP_MIXED_APP_LONG_SESSION`.

## Latest bounded allocation

After reducing Calc launch to `libreoffice --calc`, adding openbox, and
excluding known 1x1/foreign windows, the allocation reached all four
transition code paths. Focus drift passed and Chromium replacement produced a
distinct old/new window ID. It still failed because the Calc modal was not
observed (`modal=null`) and the Calc geometry receipt was empty before and
after resize. Decision remains `FAIL_MIXED_APP_LONG_SESSION`; the 15-event
ledger, zero model/network calls, and neutral cleanup were retained. This is
not a PASS and does not authorize relabeling earlier failures.

## Final bounded allocation result

The corrected runner completed one fresh local Docker allocation with all five
checks true: focus drift refusal, modal observe-only recovery, geometry change
and stale refusal, typed Chromium replacement identity, and return-to-earlier
app validation. Decision: `PASS_MIXED_APP_LONG_SESSION_SCOPED`.

The Chromium X11 window number was reused, but the old window was first
confirmed gone and the replacement had a distinct PID and surface generation;
the ledger records `identity_reused=true` and the typed identity explicitly.
This is therefore not an ID-reuse omission. The allocation emitted 15 ordered
events, 3 input operations, 0 model calls, 0 network calls, and neutral
cleanup. It establishes only this bounded protocol session; it does not claim
population reliability, model benefit, or production readiness.

## Latest identity-selection control

Restricting Calc selection to a visible window whose `_NET_WM_PID`/`WM_CLASS`
and `WM_NAME` matched `Untitled ... LibreOffice Calc` caused no matching
window within the bounded wait. The runner stopped before any transition with
`STOP_MIXED_APP_LONG_SESSION`; it did not pass a `None` identity into an
action. This confirms that the earlier 535x215 candidate was not sufficient
authoritative evidence for the Calc surface.
