Saved-only diagnostic executed once on 2026-10-04; exit0. No game/model/input.

Command: `wslc run --rm --pull never --network none --user 65534:65534 --cpus 1 --memory 512m --workdir /out --mount type=bind,source=<experiment-root>,target=/study,readonly --mount type=bind,source=<experiment-root>/saved-hud-probe-01,target=/out --env PYTHONDONTWRITEBYTECODE=1 --env PYTHONPATH=/study/current-controller-source-09/research/doom sha256:94014a0f7757b46b7c3ae83f430ad973ae6abe1722937bdc6d060139aaeb6378 timeout 20s python3 /study/probe_saved_hud_01.py`

Actual experiment-root: `C:/Users/junny/Documents/Codex/2026-09-19/new-chat/work/post-guard-recovery-59-4d74-20261004`. WSLc executable: `C:/Program Files/WSL/wslc.exe`.

stdout printed JSON identical to retained result.json. Tool captured exit0 and kernel warning: “Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.” This page transcribes that tool evidence; separate diagnostic stdout/stderr files were not saved. FREEZE hashes were written before command invocation; no independent prelaunch witness claimed.
