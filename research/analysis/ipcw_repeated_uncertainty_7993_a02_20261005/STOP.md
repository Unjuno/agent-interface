# A02 one-shot pre-candidate STOP

**Disposition: `STOP_CONTAINER_CLI_MOUNT_SYNTAX`; A02 is not a candidate or method result.**

The frozen `run_formal.py` made one Docker CLI attempt at 2026-10-05T08:23:12Z. The client rejected the output mount before creating/starting a container:

```text
invalid argument "type=bind,src=.../results,dst=/out,rw" for "--mount" flag: invalid field 'rw' must be a key=value pair
Usage: docker run [OPTIONS] IMAGE [COMMAND] [ARG...]
```

The candidate process therefore ran **zero** times; auditor ran zero times; retries zero. The raw `FORMAL_STARTED.json`, `RUN_RECORD.json`, exact argv, empty stdout, and Docker stderr are retained unchanged. The runner's `candidate_invocations: 1` counts its single attempted `docker run` command, not a started Python candidate; this STOP record makes that distinction explicit. No candidate output exists. A02 is not retried or relabeled. Any corrected execution requires a new allocation, new formal seed, and fresh freeze.

The preflight smoke had verified the pinned image's Python version, but did not exercise Docker's bind-mount parser. The missing mount-syntax preflight is the execution defect; no scientific conclusion follows.
