# MAP01 V39 r02 cleanup verifier reconciliation

This read-only posthoc audit reconciles the retained
`map01-v39-current-main-threat-live-20261024-r02` cleanup receipt with its
preregistered source identity, raw files, and the current event-specific owner
validator. Run from the repository root:

```powershell
python research/doom/audit_r02_cleanup_verifier_reconciliation_v1.py
```

The result is recorded in `audit.json`. The auditor verifies the retained
evidence digests in both LF and CRLF representations, replays the historical
generic-`verified` owner predicate against the exact preregistered Git source,
and checks each retained owner row with current main's
`owner_event_verified` implementation.

## Result

`RETAINED_CLEANUP_FALSE_NEGATIVE_RECONCILED`: all ten retained owner rows pass
the current event-specific validator, the last owner row records a verified
`reason=close`, and all non-owner cleanup components are true. The historical
predicate nevertheless returns false because it requires every row to carry
`verified=true`; the four explicit key-up rows instead carry
`server_keyup_verified=true`. This explains the retained
`owner_events_closed=false` and `cleanup_complete=false` receipt values as a
verifier false negative. The original receipt and raw evidence remain
unchanged.

The retained key-lineage audit reports five verified X-server key releases,
242 independent scorer samples, no observed useful progress, zero kills and
deaths, and no MAP01 exit. This reconciliation does not establish physical-key
release, game input consumption, the cause of the retained `RuntimeError`, a
causal performance benefit, or completion of the MAP01 or project goals.
