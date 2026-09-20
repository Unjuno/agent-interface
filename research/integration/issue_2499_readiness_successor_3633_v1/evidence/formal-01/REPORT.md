# Issue #3633 — readiness identity v4 formal-01

## Final classification: HOLD_PROCESS_LIFECYCLE_UNVERIFIED

One frozen OrbStack/Docker run executed on `mixed-app-identity-2782-local`
(Linux/arm64, image ID `sha256:e6ced3789130dae21c7b42b7b9d25cd590a271a77910e16e01d2edf87e44cee6`),
with network disabled, a read-only root/source, and a fresh evidence mount.
The raw result contains stable, unique, same-display identities for Inkscape,
LibreOffice Calc, and Chromium in two snapshots. The existing typed identity
gate admitted them; its four negative controls passed. Forbidden operation
counters are zero for geometry, focus, input, model, and network. The Xvfb
socket disappeared after cleanup.

The runner and its first independent auditor both reported
`PASS_READINESS_IDENTITY_V4_SCOPED`. A post-formal adversarial lifecycle review
found that this PASS was not supported by the preregistered cleanup gate:
Inkscape's and Chromium's visible-window owner PIDs match their launched and
reaped process records, but Calc's window owner PID is 95 while the tracked
LibreOffice launcher PID is 66 (launcher return code 255). The raw record has
no exit/reaping evidence for PID 95. The original auditor checked only the
tracked launcher list and X socket, so it missed this gap. Its pass is retained
unchanged in `audit.json`; the correcting review is `audit_lifecycle.json`.

Therefore the identity observations themselves are valid and reproducible from
the retained raw bytes, but the allocation does not satisfy the full frozen
decision gate. Final result is HOLD, not PASS or FAIL. No rerun or tuning was
performed. Container teardown discarded any remaining process state; it does
not retroactively supply the missing per-owner lifecycle receipt.

## Counts and provenance

- Formal invocation: 1; retries: 0.
- Live identity set: 3/3 admitted; first/second selected identities identical.
- Typed negative unit controls: 4 tests passed.
- Forbidden operations: geometry 0, focus 0, input 0, model 0, network 0.
- Process lifecycle: 2/3 visible owner PIDs reconciled to launched/reaped PID;
  Calc owner PID 95 is untracked. X socket absent: yes.
- Raw SHA-256: `2cbba7489555d241ea3a6fe136e73fccde267726092a33d438e424ce42d55bf7`.
- Original auditor SHA-256: `5e3ae4d9cbc86be2d06cf2807020bb216c600bd1864334ad49f20d05d0ab3004`
  (see `SHA256SUMS`); its output is retained
  to preserve the initial decision and subsequent correction transparently.
- Lifecycle review raw SHA-256: same raw digest; final classification is HOLD.

## Scope boundary

This allocation tests only the readiness/identity prerequisite from #3633. It
does not test geometry, focus/modal recovery, stale-capability admission,
independent task effects, controller integration, or the full #2499 mixed-app
long session. A new successor allocation is required to improve process-tree
tracking before this readiness gate can satisfy its full acceptance criterion.

## Reproduction

Run the exact command in `FREEZE.json` once, from the frozen source tree and
against the pinned image. Run `audit.py` in a separate network-disabled,
read-only-source container. Then run `audit_lifecycle_review.py` against the
same immutable raw result; do not edit or rerun formal-01.
