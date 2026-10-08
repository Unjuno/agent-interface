# A13B one-shot container commands

Run from repository root after the preregistration commit and freeze manifest have been verified. Each command is a separate formal stage; execute once, preserve its exact exit status and output, and stop on any nonzero status. Do not run the candidate on the host.

All stages use the frozen Node image, no network, read-only root, bounded tmpfs/CPU/memory/PIDs, dropped capabilities, no-new-privileges, and `--rm`. Stage inputs are read-only mounts; each stage has a dedicated writable output directory.

Candidate: mount only `candidate_stage/` at `/candidate`, and `out/candidate/` at `/out`; write `choices.json`. No oracle mount exists.

Environment: mount `environment_stage/` at `/environment`, candidate `choices.json` read-only at `/input/choices.json`, and `out/environment/` writable at `/out`; write `events.json`.

Auditor: mount `auditor_stage/` at `/auditor`, candidate choices and environment events read-only, and `out/audit/` writable; write `audit.json`.

The commands below assume repository root `/Users/taka/Documents/Codex/2026-09-19/new-chat-7/agent-interface-5309-precapture-a13b`. Do not edit them after the freeze. Container labels are unique to this allocation and stage for post-run removal checks.

```sh
docker run --rm --label org.unjuno.allocation=5309-a13b-candidate --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m --cpus 1 --memory 256m --pids-limit 64 --cap-drop ALL --security-opt no-new-privileges --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat-7/agent-interface-5309-precapture-a13b/candidate_stage,dst=/candidate,readonly --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat-7/agent-interface-5309-precapture-a13b/out/candidate,dst=/out node:26-alpine@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80 node /candidate/candidate.mjs /candidate/cases.json /out/choices.json
```

```sh
docker run --rm --label org.unjuno.allocation=5309-a13b-environment --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m --cpus 1 --memory 256m --pids-limit 64 --cap-drop ALL --security-opt no-new-privileges --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat-7/agent-interface-5309-precapture-a13b/environment_stage,dst=/environment,readonly --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat-7/agent-interface-5309-precapture-a13b/out/candidate/choices.json,dst=/input/choices.json,readonly --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat-7/agent-interface-5309-precapture-a13b/out/environment,dst=/out node:26-alpine@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80 node /environment/environment.mjs /input/choices.json /environment/oracle.json /out/events.json
```

```sh
docker run --rm --label org.unjuno.allocation=5309-a13b-auditor --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=32m --cpus 1 --memory 256m --pids-limit 64 --cap-drop ALL --security-opt no-new-privileges --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat-7/agent-interface-5309-precapture-a13b/auditor_stage,dst=/auditor,readonly --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat-7/agent-interface-5309-precapture-a13b/out/candidate/choices.json,dst=/input/choices.json,readonly --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat-7/agent-interface-5309-precapture-a13b/out/environment/events.json,dst=/input/events.json,readonly --mount type=bind,src=/Users/taka/Documents/Codex/2026-09-19/new-chat-7/agent-interface-5309-precapture-a13b/out/audit,dst=/out node:26-alpine@sha256:0b36e8c136b94cd4fcf02188228e76c31ad5872eef3fec8cbd2eee500cfd9e80 node /auditor/auditor.mjs /auditor/cases.json /auditor/oracle.json /input/choices.json /input/events.json /out/audit.json
```
