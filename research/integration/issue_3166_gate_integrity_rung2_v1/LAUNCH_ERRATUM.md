# Pre-formal launcher erratum

The first host `docker run` invocation for allocation
`issue3166-gate-integrity-rung2-20260927-01` exited 125 during CLI argument
validation. Docker rejected the bind-mount field `rw`; no container object was
created and the fresh evidence directory remained empty. Therefore no formal
measurement or case was executed by that invocation.

The intended writable bind mount is represented by omitting a read-only flag:
`--mount type=bind,source=<fresh-empty-evidence-dir>,target=/evidence`. Docker
bind mounts are read/write by default. This erratum changes only launcher syntax;
the pinned source, image, readonly source mount, parameters, matrix, gates,
runner, auditor, and evidence protocol remain unchanged. The one scientific
formal allocation has not yet started and will be run once using the corrected
equivalent mount spelling. The original rejection is retained verbatim in
`results/launch-stop-20260927-01/DOCKER_CLI_STOP.md`.
