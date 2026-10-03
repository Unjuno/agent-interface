# Scorer terminal-statistics repair under #59 / PR #6913

Returning scorer callbacks must still reach ready commands, while a terminal summary must account for periods the unchanged next-sample rule would mark skipped. Prior immutable head8f5872874760b671b558a7febe4e14a23261d753 contains the exact #6896 v2 adoption and original integration evidence. Review4171685391 exposed an omitted pending contribution when FINISH/EOF/sample cap prevents the next sample. New ordinary firstRED preserves13 failures across6 methods, including an actual fake-v13/real-ScorerFileSink summary reporting0 instead of2.

The runtime repair changes only final polling statistics and the stdin stats snapshot. The snapshot adds pending skipped periods without advancing the scheduler or accumulating twice. Removing those precise additions returns byte-for-byte prior deployed modules, as SOURCE.json verifies. Prior timestamps, sample receipts/skips, command/I/O paths, ownership, no-catch-up scheduling, buffer/UTF8/EOF/cap behavior remain unchanged. The new six-method regression retains original controls, adds terminal/snapshot/continuation checks and strengthens v13 composition with a three-period overrun.

Existing late-sample semantics define elapsed=floor((now_ns-next_sample_ns)/period_ns)+1 and skipped=elapsed-1 when due. A snapshot therefore adds pending=max(0,floor((now_ns-next_sample_ns)/period_ns)), keeping the current eligible slot. For a first sample/sink ending at3 periods, next deadline is1 period and pending is2. A later due sample commits the same2, so repeated snapshots and subsequent sampling do not double-count. This preserves the existing skip convention; it is not a hard deadline/lateness guarantee or a reconstruction of every physical observation opportunity.

| Symbol | 日本語の意味 | SI単位・保存単位 | 前提・型 |
|---|---|---|---|
| now_ns | 統計観測時刻 | s、整数nsで保存 | 同一単調時計、整数スカラー |
| next_sample_ns | 次の予定サンプル時刻 | s、整数nsで保存 | 開始後の予定時刻、整数スカラー |
| period_ns | サンプル周期 | s、整数nsで保存 | 正整数、ここでは10Hzで100000000ns |
| pending | 次の計数まで未反映のスキップ周期 | 1、無次元 | 非負整数スカラー |

The timestamp difference divided by the period is dimensionless; flooring and clipping preserve the integer count. Before sampling starts, stdin pending is0. Already emitted receipt rows are unchanged; total stats may additionally include the terminal pending contribution.

Combined40-method source/clock/adapter/replay/composition suite passes38 with2 explicit Windows POSIX-pipe skips, both normal and-O. All six original/renewed local unit methods are included; the firstRED is not relabeled. Exact command/UTC/exit/source/log receipts and public/private derivative joins are retained. Ordinary invocation is python -B -m unittest -v test_scorer_command_service_01a0ff58 in an isolated source closure; the archived helper records the combined suite and Windows skip policy. No original #6896/#6907 producer, auditor/mutation, formal/live allocation or native/game/model/input experiment is replayed. Actual v12/game/backend behavior, OS-pipe execution of this revised source, useful game feedback, strict real-time bounds, latency/token/efficiency benefit and R134/#57 closure remain unverified.

Both initial #6896 v2 and root v1 source/evidence remain immutable. External native assays frozen to8f587/v2 keep their original pins; they are not retargeted to this repair. Prior v1 content approval does not transfer. A new fixed head/diff/proposal/committee and two actual eligible content votes, followed by actual current-main nonauthor linkage/rules/conditional forward application, are required.
