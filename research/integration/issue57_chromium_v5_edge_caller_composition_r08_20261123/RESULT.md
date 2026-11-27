# R08 result — STOP_PREFLIGHT_INDENTATION_ERROR

R08 did not execute. Its required pre-run `py_compile` check found an
indentation error in the newly added scoped cleanup call (`expected an
indented block after 'try'`). No unittest ran and Edge was not launched. The
defect was corrected in the working tree; the corrected source will be
evaluated as a separate R09. R08 has no product outcome.

The failed preflight output and exit code are retained in [`raw/preflight/`](raw/preflight/).
