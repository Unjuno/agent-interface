# V39 cleanup actuation-identity guard A04

## H / T / D / C / U

- **H:** Cleanup is contextualized by actuation ID alone, even when the source row's owner/key/intent differs from the admitted identity; consulting the exact active identity map should route mismatches to unscoped telemetry without retiring the valid actuation.
- **T:** Seed one admitted F8 actuation, then directly deliver owner cleanup records with a reused actuation ID and one altered identity field. Compare frozen A03 with an additive A04 bridge successor. No actual owner or display runs.
- **D:** PASS only if A03 contextualizes at least one mismatched row and consumes its context, while A04 emits it unscoped, preserves the active F8 actuation/held state, and still contextualizes a matching source row exactly once.
- **C:** Synthetic malformed-source boundary experiment; determines whether the bridge prevents false attribution if owner telemetry violates identity lineage.
- **U:** Does not establish that InputOwner emits malformed IDs, real X11/input behavior, app effect, useful feedback, recovery, threat response, or MAP01 progress.

## Evidence

`SOURCE/A03/bridge_a03.py` is the frozen predecessor. The A04 successor requires
the measurement identity tuple, bracket identity tuple, active actuation map,
and actuation context to agree before forwarding a contextual release. A
mismatch remains visible as `input_cleanup_unscoped`; it cannot retire a
different held actuation. The positive control verifies valid cleanup still
forwards contextually.

Run `python3 build_freeze.py`, then the pinned one-shot `probe_a04.py --out
/tmp/a04-out`, `audit_a04.py --out /tmp/a04-out`, and normal/optimized
`test_a04.py`. One probe invocation executes five deterministic method cases
per arm (owner, intent, key, bracket mismatch and valid positive control). It
uses only an in-memory stub. Do not rerun it after a candidate outcome is
retained.
