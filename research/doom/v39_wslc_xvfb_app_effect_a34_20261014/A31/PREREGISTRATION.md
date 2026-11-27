# A31 preregistration

Unique allocation: `MAP01-V39-WSLC-XVFB-APP-EFFECT-A31-20261014-01`. A30 is a preserved pre-dispatch HOLD and will not be retried. Hypothesis and thresholds match the A30 preregistration: one admitted `a` key to a synthetic X11 app, task counter 0→1 within 200 ms, 300 ms owner lease, matching app/server release and strict known-empty terminal receipt within 1 s, owner close/thread stop, clean Xvfb exit, all checksummed source fixed.

Changed setup: use local Unix-domain X11 display `:143` with TCP disabled; run as image default root (no `su` or assumed `user` account); use the image's existing `/usr/bin/xkbcomp` or the read-only runtime PATH without creating/removing symlinks; do not call `ip`. One WSLc container, `--network none`, image ID fixed to `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592`, `--pull never`, 1 CPU, 1 GiB requested memory, output path new and empty. No game/model/Windows GUI/physical input. No retry of A31 under any outcome.

PASS only if the independent saved-raw auditor accepts every preregistered condition; setup stop before input is HOLD; any failed criterion after dispatch is FAIL. Preserve raw and logs.
