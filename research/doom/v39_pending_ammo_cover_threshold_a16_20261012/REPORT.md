# A16 result — soft/hard ammo boundary during pending turn

The final frozen WSLc run passed both cases. From source ammo 6, a newer paired observation with ammo 4 is above the cover guard floor 1: the real current-main pair monitor records one soft event and does not interrupt. The real persistent adapter accepts the synthetic completed response, then final action admission rejects its authored minimum-ammo-5 shot (`REJECTED_ACTION_NOT_CURRENT`, `ammo_minimum_failed`).

At current ammo 0, the same monitor returns `paired_signal_invalidation` (`ammo:below_hard_minimum`, floor 1). The adapter's interrupt callback ran before the fake transport's interrupt request; the transport then reported wire completion, but the adapter returned `answer_eligible=false` with `answer belongs to an invalidated observation`. No final action admission occurred.

Disposition: `PASS_CONSTRUCTION_ONLY_SOFT_HARD_PENDING_TURN_BOUNDARY`. Both arms have `executor_admission=null` and `input_authority_admitted=false`. The hard branch models adapter interruption only; it does not include controller executor cancellation or terminal physical-release verification. No model, game, GUI, OS input, feedback efficacy, recovery, progress, survival or MAP01 outcome is established.

WSLc warned swap-limit support is unavailable and memory was limited without swap. No cgroup enforcement claim is made. Raw transcript, structured result, source freeze, audit and checksums are retained beside this report.
