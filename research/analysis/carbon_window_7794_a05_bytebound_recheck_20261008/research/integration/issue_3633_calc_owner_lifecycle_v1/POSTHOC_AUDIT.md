# Posthoc independent audit

The formal container completed with runner decision
`HOLD_PROCESS_OWNERSHIP_UNRESOLVED`, raw digest
`6d110e3f3b7cbc0d1b970b50fb35a8d242c9cddb416190237419f78be8760824`.

A separate network-disabled container mounted the source and raw JSON read-only
and executed `audit.py`. It independently recomputed the same HOLD, verified
raw integrity and source/image provenance with no errors, and detected all six
corruption challenges (forged owner PGID, retained owner, retained XID, killed
sentinel, retained group member, and raw-digest mutation).

The raw timeline shows the launcher process itself (PID 12, shell wrapper
`/usr/bin/libreoffice`) as the zombie group member. Review of the frozen runner
shows it sampled the group for up to five seconds before calling `launcher.wait`.
Therefore the HOLD remains correct for the preregistered “all group members
vanish within five seconds” rule, but the zombie may reflect delayed direct
child reaping by the observer, not a live Calc process. Issue #3657 tests this
measurement-order ambiguity as a distinct successor; this does not revise the
formal-01 decision.

Result JSON:

```json
{
  "corruption_challenges_detected": {
    "group-retained": true,
    "owner-group-forged": true,
    "owner-retained": true,
    "raw-digest-mutation": true,
    "sentinel-killed": true,
    "xid-retained": true
  },
  "decision": "HOLD_PROCESS_OWNERSHIP_UNRESOLVED",
  "errors": [],
  "raw_integrity_verified": true,
  "raw_sha256": "6d110e3f3b7cbc0d1b970b50fb35a8d242c9cddb416190237419f78be8760824",
  "runner_decision": "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
}
```
