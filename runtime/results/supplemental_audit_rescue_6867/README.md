# Supplemental audit rescue #6867

Preserves all 13 package blobs from remote tip
`329b0ee11b02d50ae559abc243a30017f543bef2` without rewriting old evidence.
The existing analysis index is regenerated, not replaced by the stale branch index.

H/T/D/C/U remain in the original PROTOCOL.md. Recovery rechecks the 12 manifest
entries, three replay source pins, five publication receipts and complete
128-row raw-only replay against the unchanged main input. Original 13 tests
are also executed with RETAINED_RAW explicitly supplied. No original candidate,
formal/container allocation or legacy producer is re-executed.

The historical SHA256SUMS uses CRLF. A literal macOS shasum invocation treats
CR as part of each filename and fails to open files. The separate archive test
parses line terminators while hashing the unchanged file bytes; the manifest
itself is never normalized. Red-stage failures and publication redactions stay
visible. A soft/stateless tie is not incremental policy benefit, live safety,
GUI/task-effect or product qualification. Original committee records are not
approvals for this new delivery.

Run `python -m unittest discover -s runtime/results/supplemental_audit_rescue_6867 -v`.
