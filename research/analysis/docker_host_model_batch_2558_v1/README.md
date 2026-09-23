# Docker-to-host model batch (#2558)

Six retained Docker-native observation images were sent through the host-local
`codex.exe` bridge. Four outputs passed the compiled grounding validator and
two were rejected because the model returned identical field and submit
coordinates. Rejected calls were not retried. No output was given authority
and no GUI action was emitted.
