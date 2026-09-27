# Formal allocation 01 — STOP before container creation

Classification: `STOP_DOCKER_MOUNT_FLAG_SYNTAX`.

The frozen runner was invoked once on 2026-09-26 against the pinned Docker Desktop 28.5.1 engine and image. It created the reserved host output directory, then Docker rejected the first `docker run` command before creating a container because `--mount` does not accept the `rw` field. The runner's PowerShell error policy stopped execution at the Docker call. No formal test case ran; the container name was not created; no broker or fake executable was invoked. The allocation is consumed and must not be rerun at this output path.

Raw command/error excerpt from the tool result:

```text
docker.exe : invalid argument "type=bind,source=C:\\Users\\junny\\Documents\\Codex\\2026-09-21\\agent-interface-3808\\research\\integration\\host_broker_exit_contract_dockerdesktop_v1\\formal\\dockerdesktop-20260926-01\\raw,target=/evidence,rw" for "--mount" flag: invalid field 'rw' must be a key=value pair
At run_experiment.ps1:94, $console = & docker @imageArgs
```

The directory initially contained no Docker stdout, inspect, run receipt or raw case records. This retained STOP note is not evidence for or against the broker hypothesis. Construction repair and any subsequent formal execution require a new, prospectively frozen allocation ID and distinct output path.
