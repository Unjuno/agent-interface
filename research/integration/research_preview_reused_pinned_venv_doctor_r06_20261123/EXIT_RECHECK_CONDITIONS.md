# Doctor return-code audit R06-02

- Source and environment are unchanged from R06-01: main 7e9caab2acf8428beeb48682edd5e7a0bace4967, preserved R05 venv, Windows Chrome path override.
- R06-01 shell wrapper captured exit status as 0 despite doctor JSON passed=false. This is inconsistent with golden_desktop_demo_v3.main returning nonzero for failed doctor results.
- One parent-subprocess capture is run to preserve the direct process stdout, stderr, and actual return code independently of shell status expansion.
- No runtime setup, install, GUI action, model call, or live task.
