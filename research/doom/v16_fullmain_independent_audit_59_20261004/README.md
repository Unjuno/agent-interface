# Independent audit of V16 lifecycle evidence

This additive, author-written separate audit re-reads the two retained no-action
constructions in `research/doom/v16_fullmain_59_4d74_20261004/` and the actual
one-hold construction in `research/doom/v16_one_hold_59_4d74_20261004/`. It
verifies both source-package file inventories, preserves construction01's
undelivered-finish STOP, and joins construction02's delivered `finish`,
post-control score, two independent scorer samples, zero-event summary, and
verified-empty owner close.

For the one-hold record, the audit confirms one accepted input, one admission,
one release transition, one owner key-up request, 17 scorer samples, a changed
frame, and zero useful events. Admission, release batch, and nested owner
receipt carry matching owner, intent, id, step, and key identity. The owner
receipt says server sync completed but `physical_verification_authoritative`
is false, and the release transition has no physical-edge measurement. The
identity-bound synchronization receipt therefore does not certify the physical
key-up interval, although a later owner-state sample verifies no keys remain
down.

Run from the repository root:

```powershell
python -B research/doom/v16_fullmain_independent_audit_59_20261004/audit.py --repo .
python -B -m unittest discover -s research/doom/v16_fullmain_independent_audit_59_20261004 -p 'test_*.py' -v
```

The audit is intentionally narrow. Construction02 contains no accepted input;
its two samples and zero positive events do not establish a useful task effect.
Its post-control score precedes the verified-empty close, which is scoped to
that no-action record. The one-hold changed frame is not useful feedback. This
audit establishes no threat response, bounded recovery, causal task effect, or
live-allocation qualification. The formal Issue #59 allocation remains
unassigned.
