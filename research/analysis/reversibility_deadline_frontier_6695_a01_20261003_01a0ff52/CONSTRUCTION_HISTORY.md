# Construction history before formal freeze

- Initial fixture-generation invocation hit macOS Apple developer-tool Python/Xcode-license dispatch; no fixtures/candidate ran. Explicit Homebrew Python 3.14.5 generated the inputs. No Xcode license or system setting was changed.
- Host construction: six tests passed, including seven corruption controls.
- Shared OrbStack Docker image inventory reported a content-store blob error. No shared daemon, container or image was changed.
- A new owned `--isolated` Ubuntu VM with private Docker 29.1.3/runc 1.3.4 downloaded the Python base. One construction container failed before process launch (exit 125): `bpf_prog_query(BPF_CGROUP_DEVICE) failed: operation not permitted`. Formal candidate/auditor counts remained 0/0. Exact error is retained below. The VM was stopped.
- OrbStack's issue #2429 independently documents this isolated-machine Docker launch failure: https://github.com/orbstack/orbstack/issues/2429 . This is supporting runtime context, not host-specific proof or scientific evidence. No privileged container, BPF/sysctl change or security bypass was used.
- Creating a normal-mode VM with `--mount` was rejected by the CLI (`--mount requires --isolated`) before creation. A normal-mode owned VM was then created through its supported interface; host integration exists, so it is not described as an isolated machine. The experiment's Docker namespaces/read-only mounts/no-network boundary is separately checked. Only specifically bound synthetic inputs reach the formal candidate.

First construction launch error:
```
docker: Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: error during container init: error setting cgroup config for procHooks process: bpf_prog_query(BPF_CGROUP_DEVICE) failed: operation not permitted
```
