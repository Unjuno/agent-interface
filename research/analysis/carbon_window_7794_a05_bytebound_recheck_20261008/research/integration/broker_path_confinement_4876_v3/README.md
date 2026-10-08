# Broker path-confinement construction (#4876)

Prior local setup attempts are preserved in the Issue: allocation 01 stopped before rows because the mounted output path already existed; allocation 02 stopped before rows because read-only root had no writable temp directory. Neither invoked a case or mocked CLI. No allocation was retried.

Allocation 03 adds a private writable tmpfs at /tmp and passes a fresh nonexistent /out/formal child to the runner. Scientific H/T/D/C/U and gates are unchanged. Exact current-main broker source and the candidate path-policy matrix are copied byte-for-byte from v2; the new allocation/source/image command is frozen independently before its sole run.

This is candidate code only, not a production patch. Model allocation #3152 remains untouched. No hosted workflow/CI is used.


