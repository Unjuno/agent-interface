# Aggregate release-order observability — analytical construction A01

Parent: #57; explicit residual of merged #6861 / closed #6855, alongside the retained #5156 owner-timestamp work. Existing worker registration: https://github.com/Unjuno/agent-interface/issues/5156#issuecomment-5963705617 . Claim: https://github.com/Unjuno/agent-interface/issues/57#issuecomment-5964860110 . Branch: research/57-release-order-observability-5156-20261003.

## H — claim under test

At selected primary main 332da58a9b6b825c384a142dfb59d7ed2b8b774e, aggregate ExecutionReceipt fields can be identical for a model history with empty terminal input and another with a press after the recorded verified-empty release. A receipt-only decision cannot distinguish such histories. Requiring release.observed_ns >= execution.ended_ns is a simple conservative comparator, but may refuse legitimate last-input -> release -> bookkeeping histories. A complete event-order witness is a descriptive comparator with extra information; its agreement does not demonstrate equal-information superiority or confer authority.

## T — fixed finite first rung

Exact four primary kernel Git source blobs are exported, never modified. The earlier literal construction used6da2b492; all four original source bytes/identity are retained under construction_sources/. Before the primary freeze, #6859 advanced main to332da58a. __init__, contracts and lifecycle remain exact bytes; only unused BackendRegistry.create gains the reviewed method-callability guard. That guard is never invoked by this assay. The selected primary source was updated before execution; no primary candidate/auditor existed yet and decision gates/inputs were not changed. cases.json fixes 36 histories: two recorded end timestamps; three press timestamps; release at each of three interior timestamps, at end, or after end; both explicit orders when press/release timestamps tie. Initial A is up; one press holds A; release-all makes A up at that event; no external or unlogged input. A verified-empty snapshot is true at its release event, with no promise about later events. Receipt delivery occurs after every listed event. The finite model therefore tests information sufficiency without assuming a broken physical backend.

Candidate imports the isolated exact kernel, constructs valid typed observation/binding/lease/request/receipt, records fresh unavailable effect evidence, and reads the actual terminal outcome. Kernel inputs contain no press timestamp or event sequence. Compare actual release_verified, the timestamp-only end floor, and last-input sequence < release sequence. The latter consumes extra descriptive information only in this research comparison; privileged trace state is not added to a controller.

Write source, cases, candidate, independent raw-only auditor, construction tests, runner and this plan before a freeze. Construction tests check literal histories/types/projections without invoking the 36-row primary CLI. One primary candidate CLI, then one raw-only auditor CLI, at unique run01; no retries or replacements. Each own child has a 15-second diagnostic timeout; preserve partial streams and terminal code if reached. Output budget <2 MiB; one native CPython process at a time, stdlib only. This is the RESEARCH_METHOD finite analytical route, not a formal/live/container allocation or wall-time benchmark. All first outcomes remain retained.

## D — prospectively fixed decision

Integrity PASS requires exactly 36 original rows, all source/freeze/case hashes, independent typed event reduction, exact projected receipt identity, actual outcome and comparator reconstruction; 12 effective copied-raw corruptions must reject. Model result FAIL_TERMINAL_RELEASE_IDENTIFIABILITY requires at least one exact full-receipt equivalence class with opposite independently reduced terminal states. If no such class exists, REFUTED; missing/contradictory data are HOLD. Source behavior/false-release counts are reported as observed, without changing thresholds. The expected analytical domain predicts six mixed projection classes, 12 current-kernel false terminal-release reports, 12 safe histories refused by the end floor, and zero descriptive ordered-witness disagreements; these are prospective predictions, not measurements.

## C — strong simple alternatives and assumptions

The start lower bound already repairs pre-start snapshots. The end floor can conservatively refuse all interior-release histories. Trusting a backend's stronger terminal-release guarantee may make the ambiguity unreachable; this assay does not show any real backend violates that guarantee. The end timestamp can include post-release bookkeeping, so replacing the existing lower bound with an end bound is not automatically a correct runtime repair. Equal timestamps do not imply equal event order. Completeness, ordering and provenance of any extra witness are assumptions, not proved authentication.

## U — limits and empirical residual

Finite synthetic one-key/common-clock/sequential source construction. No operating backend, actual release, scheduler, clock provenance, cross-owner concurrency, adversarial logging, unlisted operation, model, task success, tokens or latency was measured. No runtime/API/workflow/index change or promotion is proposed. This cannot quantify probability or establish that physical input remains held on any host. All original allocations and records are unchanged.

| 記号 | 日本語の意味・定義 | SI 単位 | 範囲・前提 | 型 |
|---|---|---|---|---|
| S | 記録された実行開始 | s（保存値は ns） | 100 ns、共通時計の有限モデル | 整数 scalar |
| E | 記録された action phase の終了 | s（保存値は ns） | 700 または 900 ns、全 press より後 | 整数 scalar |
| P | 1 回の modeled press の時刻 | s（保存値は ns） | 200 / 400 / 600 ns | 整数 scalar |
| R | release-all と空状態観測の時刻 | s（保存値は ns） | 200 / 400 / 600 / E / E+100 ns | 整数 scalar |
| j | 明示的な event 順序 | 1（無次元） | 各履歴で一意な 1..4、同じ時刻の順序を表す | 整数 scalar |
| K | 最終時点に A が held か | 1（無次元） | 完全な modeled event 列だけから独立再構築 | Boolean scalar |

時刻比較は同じ ns scale の整数間で行い、1 ns = 10^-9 s。観測された実時間や測定誤差の推定ではない。
