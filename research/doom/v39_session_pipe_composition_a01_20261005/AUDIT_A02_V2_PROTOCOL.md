# Versioned A02 raw audit repair

The candidate A02 run completed once and is unchanged. Audit V1 stopped on a
checker assumption: it looked for the retained event's hash in the source-code
hash map instead of the separate input hash field. The exact V1 error remains
in `AUDIT_A02_ATTEMPT_V1.txt` and its disposition record.

Audit V2 changes only this read-only saved-result check. It treats the
`published-events.jsonl` event as the frozen input, then independently checks
the input bytes, exact source refs/blobs, actual child stdout line, writer and
delivered files, controller-decoded row, authority flags, process exit/stderr,
runner receipt, and the candidate/auditor hashes. It does not invoke or rerun
the candidate process. The auditor hash and candidate output hashes are
prospectively recorded for this audit invocation in
`AUDIT_A02_V2_FREEZE.json`.
