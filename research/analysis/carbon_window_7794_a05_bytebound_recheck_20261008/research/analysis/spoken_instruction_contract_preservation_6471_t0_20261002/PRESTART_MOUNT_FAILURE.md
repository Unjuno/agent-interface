# Pre-process WSLc mount failure — retained reconstruction

The first `wslc run` attempt exited 1 during OCI container initialization, before the candidate Python process was created. The attempted layout mounted `/src` read-only and separately bind-mounted a writable host file at `/src/candidate.raw.json`. WSLc could not create the nested file mountpoint because its parent mount was read-only:

```text
wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.
failed to create task for container: failed to create shim task: OCI runtime create failed: unable to start container process: error during container init: error mounting "/mnt/{...}/candidate.raw.json" to rootfs at "/src/candidate.raw.json": create mountpoint for "/src/candidate.raw.json" mount: make mountpoint "/src/candidate.raw.json": read-only file system: unknown
E_FAIL
```

The command returned exit 1 and the candidate output file remained zero bytes. No Python entrypoint ran in this failed start. The temporary stderr file from that first attempt was overwritten when the one permitted candidate process was later started using a separate writable execution copy; consequently, the exact error text above is transcribed from the tool output retained in the task transcript, not a preserved original stderr artifact. The successful candidate and independent-auditor stderr logs are preserved separately. No scientific result depends on the failed start.
