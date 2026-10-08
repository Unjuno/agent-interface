# Tk first-character successor allocation A01 — preregistration / HOLD

Status: **HOLD_NOT_AUTHORIZED**. No formal input trials were run. This is a
prospective allocation proposal linked to [Issue #5260](https://github.com/Unjuno/agent-interface/issues/5260)
and [successor #5296](https://github.com/Unjuno/agent-interface/issues/5296).
The existing #5296 T0 result and #5260 historical allocations are not changed,
replayed, pooled, or treated as authorization for this proposal.

## H / T / D / C / U

**H.** In a fixed disposable Tk/Xvfb application, target-entry first-character
delivery and exact saved text may vary with child-vs-managed-relative click
coordinates, click-to-first-key delay, and bounded CPU load. Dispatch receipts,
Tk KeyPress/focus events, first post-key XWD frames, and final saved values are
distinct endpoints.

**T (proposed only).** One fresh allocation, 96 trials: coordinate method
`CHILD_ROOT_COORD` vs `MANAGED_RELATIVE_COORD` × first-key delay 0/50/100 ms ×
idle/one bounded CPU worker × 8 replicates/cell. Each trial launches one fresh
private Tk app, waits for observed Map and Configure and positive geometry,
injects `hxy` with 20 ms inter-key gaps, captures the first post-KeyPress XWD,
then clicks Save after 250 ms. The app is only a local disposable fixture.
Candidate and read-only auditor run in separate network-disabled bounded
OrbStack containers. Candidate source, auditor, fixture, image digest, absent
output path, commands, and decision rule must be frozen before any formal run.

**D.** Formal integrity PASS only if all 96 scheduled rows are represented;
Map/Configure and accepted geometry precede each click; coordinate derivation,
dispatch count/delay, app/widget key events, first-frame bytes/hash, exact final
saved text/count, and clean bounded worker exits reconstruct with zero audit
errors. The scientific outcome is reported per cell; OCR is exploratory and an
OCR UNKNOWN/mismatch is retained, never silently converted to a match. No
causal or generalized readiness claim from this single fixture.

**C.** Child-vs-managed coordinate derivation, app focus handling, Xvfb/Openbox
event scheduling, host/container load, and synthetic payload/task behavior can
explain differences. XTEST dispatch is not proof of app receipt; a Tk event is
not proof of a useful visual acknowledgement; final exact fixture save is not
general application correctness.

**U.** One Python 3.12/Tk 8.6/Xvfb/Openbox linux/arm64 environment and one
disposable app only. No user display, real task, production UI, model, network,
human, external effect, automatic replay, product readiness, broad GUI
reliability, or human-tempo inference. OrbStack CPU/memory flags alone do not
prove host resource enforcement.

## Allocation identity and current gate

- Proposed allocation: `tk-firstchar-map-barrier-5260-a01-20261002-01`
- Branch: `research/issue5260-firstchar-a01-20261002`
- Additive path: `research/integration/tk_firstchar_5260_a01_20261002/`
- Base: `f303f2f57baecd95f0dc5ef6bc063a29a63c90c3`
- Construction image currently tested: `sha256:29b4131f68497276cdebc816b6e3a50354a459064edbff57538340fd3ab54118` (linux/arm64)
- Formal allocation status: **NOT STARTED**. Do not run until the Issue owner
  explicitly authorizes this fresh allocation and the allocation gate is
  prospectively updated. An Issue comment requesting authorization does not
  itself grant it.
- If authorized, freeze exact source/image hashes and unique empty output path,
  execute candidate once, then execute the independent audit once. Preserve
  every first outcome; no formal retries or output replacement.

## Construction-only records (not formal evidence)

- `construction/smoke-01/`: candidate returned success; first audit failed on
  XWD audit-path/integrity assumptions and unresolved OCR. Preserved.
- `construction/smoke-02/`: candidate returned success; audit caught the
  baseline XWD hash mismatch and the candidate schema mismatch. Preserved.
- `construction/smoke-03/`: candidate returned success; after scoped auditor
  corrections, independent audit returned `PASS_AUDIT`, errors `[]`, one of one
  exact save, first Tk key on target Entry, and first-frame XWD hash verified.
  OCR did not resolve `h`; baseline XWD hash remained unstable and is excluded
  from the gate, reported as 0/1 integrity. This is runner/auditor construction
  evidence only and is not pooled into the proposed 96-row allocation.
