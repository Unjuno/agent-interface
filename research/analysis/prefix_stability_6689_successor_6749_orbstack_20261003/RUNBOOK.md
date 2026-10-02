# OrbStack runbook — Issue #6749

Use only the local image `python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e` (linux/arm64); pull is forbidden. Engine is OrbStack Docker Engine 29.4.0. Network is disabled, rootfs read-only, 1 CPU, 256 MiB memory, 64 PIDs, all capabilities dropped, no-new-privileges, UID/GID 1000:1000. Source/fixture and candidate raw are read-only mounts. Each command has its own container and distinct output directory. Formal candidate/auditor each run at most once; any failure is retained with no retry or source change.

Candidate container command shape:

```sh
docker run --name issue6749-candidate-a01 --pull=never --network=none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --user 1000:1000 --mount type=bind,src="$PKG",dst=/src,readonly --mount type=bind,src="$OUT/candidate",dst=/out --entrypoint python python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e -B /src/candidate.py /src/fixture.json /out/raw.json
```

Independent auditor container command shape:

```sh
docker run --name issue6749-auditor-a01 --pull=never --network=none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --user 1000:1000 --mount type=bind,src="$PKG",dst=/src,readonly --mount type=bind,src="$OUT/candidate",dst=/raw,readonly --mount type=bind,src="$OUT/auditor",dst=/out --entrypoint python python@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e -B /src/auditor.py /src/fixture.json /raw/raw.json /out/audit.json
```

Before launch verify the current `origin/main` equals the frozen base, issue and PR ownership remain unchanged, image digest is present locally, and both output directories are absent. After each single invocation preserve stdout, exit code, container inspect metadata, and generated files before removing only its named container. Independently compare source/result/audit hashes against the manifest. Do not treat configured limits as measured cgroup enforcement.
