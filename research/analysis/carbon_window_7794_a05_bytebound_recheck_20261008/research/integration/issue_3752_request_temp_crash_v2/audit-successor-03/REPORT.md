# Independent artifact audit — PASS

Allocation `issue3752-request-temp-crash-audit-successor-03` completed once in a fresh pinned OrbStack container: `PASS_AUDIT_V3`, errors `[]`.

The auditor mounted the repository and formal-02 evidence read-only and wrote only `audit.json` to a distinct fresh output directory. It independently confirmed:

- formal raw SHA-256 `6d0cc630d979b19263450f8220ac0bce184e0ebdc5ea267ab76f67d1e994ea68`;
- frozen source blobs for `attempt.py` and CLI `__main__.py`, plus the frozen experiment runner SHA-256;
- exact synthetic input hashes;
- the actual `.request.json.tmp` is 134 bytes with SHA-256 `a68eae9cbd852ea5402d89c72eb4450e64021a2e300a7156480116de5a55b48c` and is the expected strict request prefix;
- status contracts and exit codes, absent final records, child exit 29, public CLI reuse refusal, and exact retained run snapshot.

Audit JSON SHA-256: `6d2a1515d3dac289701b98c98de4a64306dc30ca89c3ba20d273785b4037a5f8`.

This is an artifact audit of the single scoped process interruption. It does not broaden the formal result beyond the scope in `formal-02/REPORT.md`.
