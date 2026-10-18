# Current-main evidence rescue note

This note accompanies the original evidence package for PR #6939 and its
overlapping predecessor PR #6934. The archived source, receipts, and experiment
results are preserved as historical evidence only; no producer, auditor, GUI,
or native-input experiment was rerun for this rescue.

The package is additive on current `main` at `d6b3376aaabb6738dbf8e6a8184fe10e66aa937d`.
The runtime implementation and executable regression tests are deliberately not
included in this evidence-only change. Those changes remain subject to a
separate current-main code review and required approvals. PR #6934 remains
conflicted; PR #6939 remains a draft without an approval decision. Their
historical CI results do not constitute approval of this rescue or authorize
merging either runtime patch.

Local read-only integrity validation checked both JSON `MANIFEST.json` files
and both nested `SHA256SUMS` files: 180 archived member hashes matched. CRLF
bytes were preserved; the original evidence files were not normalized. This
integrity check does not independently establish the experiment claims or
current runtime behavior.
