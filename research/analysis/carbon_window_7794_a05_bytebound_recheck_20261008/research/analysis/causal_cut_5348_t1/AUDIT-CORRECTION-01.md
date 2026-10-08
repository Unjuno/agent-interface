# AUDIT-01 correction record

The frozen auditor source 7b7e1c23c6d28607c934036e5f64c452f3ec9c06 exited 1 with raw_reconstruction_mismatch. The independent prefix-cut and control recomputations ran, but its expected raw constructor omitted two fields that the frozen runner adds: runtime metadata and the disposition label. The byte-exact diff was limited to missing top-level /runtime and /disposition in the auditor's expected object. No row, cut, count, source identity, or side-effect mismatch was reported.

The formal runner was not rerun and RAW-01 was not modified. The original AUDIT-01 failure is retained unchanged. A separately named post-run auditor correction adds only those two runner-output metadata fields; it is not described as a pre-frozen independent audit. Final disposition remains audit-qualified / UNCERTAIN because the preregistered auditor failed on its first invocation.

The correction auditor must independently reconstruct all raw rows, verify raw SHA-256/source identity, and pass mutation controls. Its result is AUDIT-02 and does not overwrite AUDIT-01.
