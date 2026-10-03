# #59 finite command-burst / scorer service comparison

Worker: `01a0ff59-0820-7c81-8ef1-f7c3e48ab67d`, FINAL-v5. This is ordinary
CPU/stdlib enumeration in a private Windows host directory. It uses no formal
allocation, container, WSLc, game, model, GUI, native descriptor or OS input.
Deployed source, historical evidence and #6896 first FAIL remain unchanged.

H: #6896's repair_v2 removes sustained-sample-overrun command starvation, but
bulk polling dispatch and buffered-first stdin delivery can suppress the
independent scorer through a positive-cost command burst. Giving at most one
complete command between due-sample opportunities is a smaller sufficient
comparator than adding a thread or model. This concerns the independent useful
feedback measurement path, not admission authority or an observed GUI failure.

T: actual retained classes at main a394fcdd4254679df4265622b8ae6d0f8e251849,
exact #6896 fair_v2 source copies at 6a82a3ee5be8b4a0c0929ea26a882b00ac28fd4f,
and one_command copies. Cross 2 adapters x 3 arms x 4 sample costs x 4 command
costs x 4 burst lengths x 2 complete-line chunk layouts = 768 rows. Nominal
period P=100,000,000 simulated ns; sample cost 0, P/2, P, 3P/2; command cost
0, P/4, P, 2P; lengths 1/2/8/32, followed by FINISH with zero callback cost.
The sink has zero simulated cost. One combined read versus one line per read
holds identical command content/cost fixed and exposes buffering effects.

Before freezing, main advanced to 92ec265bf94697f85d8cdfecde6e2ddf17a53a88.
All three imported original scorer/progress-clock blobs are byte-identical;
the complete intervening delta contains separate clipboard evidence and core
manifest-enum repair paths, none imported by this assay or any comparator.
The private branch was advanced before freeze. A prior current-main guard
stopped before FREEZE/raw/execution creation; candidate/auditor counts were zero.

Each callback returns; a declared 64-recorded-sample budget stops a starved
trace. That diagnostic endpoint does not turn finite execution into a measured
wall-time liveness guarantee. No synthetic catch-up samples. All calls remain
on the same owner thread; scorer-only payloads never reach command callbacks.

D: keep the first complete raw output. A separately written abstract event
reference imports neither assay nor classes and must match every ordered
sample/command event, scheduled/missed period, simulated time, input identity,
I/O count and stop disposition in all 768 rows, using canonical JSON to avoid
numeric type aliases. Eight copied-raw corruptions must be rejected. The H
contrast is supported only if repair_v2 completes every finite command stream
yet admits a larger command-start sample age than one_command in positive-cost
one-chunk cases; one_command must complete all 256 cases with command sequence
preserved and age <= P+sample_cost. Otherwise retain FAIL/UNCERTAIN or the null.
Budget: raw <=16 MiB; first frozen enumeration only, no overwrite or retry.
Construction checks and ordinary repair regressions are distinct from this run.

C: coalesced transport and slow synchronous handlers, rather than a model,
explain the loss. The original stdin path already protects sampling when its
sample callback is shorter than one period. A nonreturning scorer/handler is
not repairable by this nonpreemptive ordering change. Final session sampling
may recover a terminal state while still missing intermediate feedback.

U: injected integer clock/cost, ready complete lines, no actual select/pipe,
partial/empty-line transport, source-admission effect, game workload, feedback
ground truth, OS scheduling, physical release or task-benefit measurement.
Cost distributions and burst sizes in actual model traffic remain unknown.
Do not adopt or advertise an integrated runtime repair from this comparison.

| Symbol | Japanese meaning | Unit | Definition / range | Type |
|---|---|---|---|---|
| P | 仮想サンプル周期 | simulated ns | 100,000,000; no host-time measurement | positive integer |
| sample_cost | 仮想サンプル処理時間 | simulated ns | 0, P/2, P, 3P/2; every callback returns | nonnegative integer |
| command_cost | 仮想コマンド処理時間 | simulated ns | 0, P/4, P, 2P; FINISH is zero | nonnegative integer |
| length | 終了前の操作コマンド数 | 1 | 1,2,8,32 | positive integer |
| age | コマンド開始時の最終サンプル開始からの経過 | simulated ns | start minus latest actual sample start | nonnegative integer |
