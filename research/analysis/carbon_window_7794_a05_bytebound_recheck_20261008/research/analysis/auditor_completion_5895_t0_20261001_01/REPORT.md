# Issue #5895 T0 — start-gate STOP

## Disposition

`STOP_GUEST_BOOT_CONTROL_UNAVAILABLE`; the hypothesis was **not evaluated**. Candidate invocations: 0. Independent auditor invocations: 0. Docker daemon checks and image pulls: 0. The bounded 09:00–09:25 UTC reservation was not consumed scientifically; no target fixture or mutation case ran.

## Frozen target and local construction checks

- Start main: `4b7fe7837e4ee8c0d035ebfbf52baf014f042295`.
- Target remained open PR #5630 at head `288d0498d11cf16657e523a04616bf4f49cd94f4`; the three target Git blob identities are frozen in `FREEZE.json` and are unchanged from the preregistered target.
- Fresh allocation: `AUDIT-COMPLETION-5895-T0-ISOLATED-ORB-20261001-01`.
- Before the allocation window: successor tests 10/10; target auditor tests 11/11; `py_compile`, `git diff --check`, and analysis-index check passed (306 retained result/failure directories).
- Main advanced during preparation. The branch was rebased before any candidate invocation; only `FREEZE.json` and `PREREG.md` were updated to record the new start-main SHA.

## Guest start gate

OrbStack created guest `obs-auditor-completion-5895-20261001`, ID `01M3VB1X7H2APS1MN0871NQRNG`: Ubuntu 24.04 amd64, isolated, isolated network, no host mount, no SSH-agent forwarding, one CPU, 2048 MiB RAM, 8 GiB disk cap. OrbStack reported guest state `running` by 09:01:28 UTC. The first-boot serial log continued to report `console-setup.service/start running` and `systemd-update-done.service/start running`; the guest command channel never became usable. `orbctl run ... uname -a` and `orbctl run ... id` returned no output; a bounded 30-second `id` call remained blocked. Therefore the in-guest OS, Docker Engine, empty daemon inventory, pinned image/platform, source transfer/hashes, and empty output directory could not be verified.

The gate failed before Docker or candidate execution. No shared OrbStack Docker context was used, and pre-existing guests/containers were untouched.

## H/T/D/C/U

- **H:** unchanged; whether the frozen synthetic auditor has the preregistered Python equality/cardinality behavior is unknown.
- **T:** protocol not entered. 0/8 target cases, candidate 0, independent auditor 0, retry 0.
- **D:** `STOP_GUEST_BOOT_CONTROL_UNAVAILABLE`, not PASS and not scientific FAIL. No result-dependent tuning or retry.
- **C:** one newly created isolated OrbStack Ubuntu amd64 guest; initial boot/control-channel failure. No Docker container, model, GPU, GUI, X11, game, input, networked application, or task effect.
- **U:** no inference about the target auditor or PR #5630 formal behavior. This STOP only documents failure to establish the allocated guest execution substrate.

## Preserved start-gate observations

At 09:00:07 UTC, OrbStack showed the new guest `creating`; by 09:00:45 it showed `provisioning` with 642.7 MB on disk; by 09:01:28 it showed `running`. The reported config was amd64, isolated, isolated network, SSH-agent forwarding false, CPU limit 1, RAM 2048 MiB, disk cap 8 GiB. At 09:02:22 disk usage was 759.5 MB. Through 09:03:12 UTC, boot logs still showed the two pending systemd jobs. At 09:03:12 UTC, `orbctl run -m obs-auditor-completion-5895-20261001 id` was allowed 30 seconds and remained blocked without output. The guest was left intact for evidence recovery; it must not be treated as a usable daemon or slot release until an explicit later disposition.

No GitHub Actions or remote CI were used.
