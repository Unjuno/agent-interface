# V39 per-key cleanup forwarding: raw owner-source audit A04

## H / T / D / C / U

- **H:** The retained A03 consumer-shaped release row is justified only when an identical per-key cleanup row exists in the raw owner-record stream and its samples confirm the claimed release.
- **T:** Re-audit the exact retained A03 raw/result without running the candidate. Mutate the owner stream to remove the matching per-key row and to mark its source sample failed while keeping the projected event unchanged.
- **D:** PASS only if the original frozen raw passes, both mutations are rejected, and the prior auditor is shown to accept those mutations.
- **C:** This is a raw-audit successor for a single fake-display trace; it preserves earlier A02/A03 artifacts.
- **U:** No live V39 deployment, real X11, OS input, GUI/game, model, application effect, useful feedback, recovery, threat response, or MAP01 progress is tested.

## Finding and repair

The previous A03 auditor checked that the projected event had `owner_cleanup_record.verified == true`, but did not join the release measurement to the retained `owner_records` stream. Recomputing the raw digest after removing the source row, or changing its classification and bracket to failed, still produced PASS. This successor verifies the source record equality, unique actuation match, release identity, sample availability/state/timing, bracket endpoints, and projected-field correspondence before invoking the strict consumer oracle.

No candidate or fake-display run was repeated. The original A03 raw, result, and audit are preserved byte-for-byte under `SOURCE/BRIDGE/`.

Run `python3 build_freeze.py`, `python3 -m unittest -v test_a04_audit.py`, `python3 -O -m unittest -v test_a04_audit.py`, and `python3 audit_a04.py`.
