# Docker/Xvfb caller efficiency extension R11

Purpose: add two fresh matched MAP01 pairs to R10's direct-versus-compiled observation-to-effect comparison. This remains a local descriptive experiment, not a reliability or broad efficiency study.

Arms, one attempt each, no retry: pair 3 direct then compiled (seed 2026102913); pair 4 compiled then direct (seed 2026102914). Conditions inherit R10 exactly: pinned Docker image sha256:b473b61c9dda0fab168f4a2118bd1206676dc6913122a3b9193d423426bc0b84, Xvfb :91 1280x1024x24 -cc 4, ViZDoom/FreeDoom MAP01, 600ms W-forward, one pre-baseline setup tick, one post-release spectator tick inside timed predicate/effect verification, independent X11 W-down sampling, verified empty terminal release, independent W-up, and >=0.1 MAP position change. The code is the preserved R10 harness with only pair IDs, fresh seeds, /tmp config prefix, and packet output path changed.

Timing starts at the first route observation and ends after typed effect verification. It excludes startup and alias mint/preflight. No provider/model/MCP usage.

Each arm runs once in a network-disabled, read-only-root container with source mounted read-only, evidence writable, /tmp as tmpfs, and Xvfb local to the container. Retain every outcome; do not rerun failed arms. Pretrial source and harness hashes are frozen before launch.

Scope exclusions: no Windows/WSLc transfer, blocked-I/O recovery, MAP01 completion, model/token/billing accounting, product end-to-end claim, or general reliability claim.
