# V15 private X11 qualification

Worker e0cc/root, FINAL-v5; source target owned PR #8094 head `2b0cb591c3ebcb84d1db983612613850c08fffea`. This is ordinary bounded construction, not a retry of any consumed allocation or #59's unassigned game/model lane.

H: the measured V15 backend/current V4/V3/V12 owner can preserve ordered multi-key release and identity-bound cleanup-first interruption against a real private X server. Existing fake-X execution and #8005's older one-key Xvfb owner-pair witness do not establish this combination.

T: first establish a usable owned environment. Then freeze source, driver, inputs and audit before executing a bounded normal multi-key case and a cleanup-first cancellation case. Reuse an existing native fixture where possible. Source input will be isolated from output; retained raw must never be overwritten by a rerun. Any setup failure remains evidence. The exact executable design depends on the existing native entrypoint review.

D: retain original outcome; require real X11 event/keymap evidence, receipt identity, correct release order, verified neutral final state and finite termination. A harness-only success cannot establish useful game feedback, recovery efficacy, speed benefit, physical keyboard state or MAP01 completion.

C/U: Xvfb is virtual X11, not physical hardware or game behavior. One bounded case per declared schedule is not a reliability/latency estimate. No model, GPU, game or existing foreign display/VM may be used.

Environment diagnosis at 2026-10-05 11:29 UTC: macOS arm64, physical RAM 64 GiB, 10 CPUs, memory_pressure reports93% free and df reports612648648KiB available. Default OrbStack Docker version responds; image inventory and direct inspection of one observed native image both fail with content-store operation-not-supported. No container was started. There are98 retained Docker containers, none running. Four separate OrbStack machines are running, none owned by this workspace; they will not be reused. Raw metadata remains private.

Provisioning decision: use one new uniquely named `v15-native-e0cc-20261005` Debian bookworm arm64 OrbStack machine with `--isolated --isolate-network --user study`. No host mount, SSH-agent forwarding, shared Docker repair, restart, prune, foreign-machine command, or game-lane acquisition. This is a new local machine, not another research agent. Package installation and output must stay bounded; target one test process, one Xvfb, <=1GiB working memory and <250MiB new run evidence. Stop the owned machine after saving results. Do not delete evidence.
