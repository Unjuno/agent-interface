# A05 pre-start STOP — invalid Docker mount option

- Frozen allocation: `5309-WITNESS-A05-HOSTCPU-20261007`, main `3dba6c86f212c37a2d80c844b816c38921a42cc5`, pinned image `python@sha256:c845af9399020c7e562969a13689e929074a10fd057acd1b1fad06a2fb068e97`.
- One preregistered candidate `docker run` command was attempted. Docker rejected `--mount ... ,rw` before creating/starting the container: `invalid field 'rw' must be a key=value pair`; exit 125.
- Candidate process invocations: 0. Raw output: absent. Auditor invocations: 0. Scientific result: none. Retry count: 0; this allocation is not rerun.
- This is a launcher-argument STOP, not evidence for or against H. The corrected mount syntax must be frozen under a new allocation ID/path before any execution.
- No existing container was modified or removed.
