# Run 01 STOP

Disposition: `STOP_CONTAINER_ENTRYPOINT_PATH`. The pinned container started, but Python was given a repository-relative path while the experiment package itself was mounted at `/repo`; it exited before the test module loaded. Candidate test executions: 0; auditor executions: 0. Exact stderr and process exits are retained. Run 02 used the package-root work directory and a distinct output path.
