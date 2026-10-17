# V39 renewal invalidation A01

Issue #59 successor for the distinct rejected-renewal admission ordering. See FREEZE.md, RESULT.md, and retained raw stdout files.

In a checkout of this PR branch:

```powershell
python research/doom/v39_renewal_invalidation_a01_20261005/candidate_test.py research/doom/map01_overlap_controller_v39.py
python research/doom/v39_renewal_invalidation_a01_20261005/audit.py research/doom/map01_overlap_controller_v39.py
```

The WSLc focused suite used a read-only bind mount and image agent-interface/native-suite-wslc-a08:20261004:

```powershell
wslc run --rm --entrypoint python --cpus 2 --memory 1G --mount "type=bind,source=<checkout>,target=/work,readonly" --workdir /work agent-interface/native-suite-wslc-a08:20261004 -B -m unittest research.doom.test_map01_overlap_controller_v39 research.doom.test_overlap_controller_v39_wait research.doom.test_source_refresh_v1 research.live_control.test_action_validity_admission_v1 research.live_control.test_observable_signal_guard_v2
```

Repeat the same command with `-B -O -m unittest` for optimized mode. WSLc warns that the kernel lacks swap-limit capability/cgroup; see FREEZE.md.
