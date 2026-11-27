# A07 release token ownership precheck

`token_precheck(events)` reports `HOLD_AMBIGUOUS_TOKEN` if cancellation IDs are missing or duplicated, an admission has a missing/malformed token or no matching cancellation, a cancellation uses multiple tokens, or a token is shared by distinct cancellations. A no-input cancellation does not require a token. It makes no changes to saved raw or earlier audits.

`READY_FOR_FURTHER_CHECKS` means only these token ownership checks passed. It is not a release, ordering, terminal-cleanup, event-provenance, physical-input, or task-effect verdict. The precheck does not inspect owner events or bind individual release transitions to admissions; it is not a complete successor reconciliation. Historical A07 raw was not inspected.

The synthetic tests use the retained fixture and do not start a model, GUI, game, or input allocation.
