# X11 Unicode clipboard v1 — retained first formal outcome

**Disposition:** `FAIL_FORMAL_HARNESS_RELATIVE_FILE_URI_BEFORE_INPUT`.

The source-frozen matrix started once and stopped in the Writer arm before executor/input/clipboard mutation. `run_matrix.py` passed a relative output directory; `run_arm.py` used the resulting relative LibreOffice profile path directly in `-env:UserInstallation=file://...`. Writer never published an X11 window, and the matrix could not read `writer/report.json`.

This is a formal harness failure, not a Unicode-mechanism outcome. No arm is counted as completed and the result ID will not be rerun. The successor must use a new source freeze + result ID and resolve output paths before constructing file URIs.
