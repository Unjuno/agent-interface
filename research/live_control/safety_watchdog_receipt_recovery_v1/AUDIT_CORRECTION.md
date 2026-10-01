# Read-only audit-v2 correction

No measurement, gate, threshold, schedule, or scientific source changed after formal execution.

The sole audit-v2 change is:

```diff
- j['journal_write_done_ns']
+ receipt['journal_write_done_ns']
```

in the already-preregistered ordering check:

`verified_empty < journal_write_start <= journal_write_done < recovered_publish`.

The journal row remains the authoritative persisted cleanup content. The watchdog evaluator receipt supplies the post-fsync completion timestamp. `audit_v2.py` is read-only over the retained aggregate and returned `PASS_WATCHDOG_RECEIPT_RECOVERY_SCOPED`, errors `[]`.
