# Terminal scheduler accounting: independently confirmed limitation

These are **new ordinary directed diagnostics**, executed once at 2026-10-03
04:32:53 UTC, followed by a separate saved-record checker at 04:33:21 UTC.
Original formal A01/candidate/auditor were not replayed. Runtime repair and
adoption remain owned by PR #6913; this package deploys no source.

The exact fair-v2 source adopted at head `8f5872874760b671b558a7febe4e14a23261d753`
reports zero final `missed_sample_periods` in ten returning-overrun terminal
traces. The injected clock advances 350 ms during the first sample or sink at
10 Hz. No periodic sample serves the strict-interior deadlines at 100, 200 or
300 ms before FINISH, EOF or the polling sample-count cap. Ten 10 ms controls
have no unserved interior deadline and also report zero. All 20 endpoints,
commands, one-sample bounds and owner-thread identities match the intended
construction. `independent-result.json` reconstructs the deadline grid from
saved records by enumeration, separately from the scheduler's elapsed formula.

| Symbol/field | Japanese meaning | Unit | Definition/type |
|---|---|---|---|
| period_ns | 定期標本の周期 | ns | 100000000, positive integer |
| cost_ns | 戻る標本取得または保存の注入所要時間 | ns | 350000000 or10000000, integer |
| initial_ns | 診断開始時計 | ns | 0, integer |
| ended_ns | 終了境界の注入時計 | ns | equal to cost_ns, integer |
| unserved deadline | 終了前に経過し標本未取得の周期境界 | ns | grid strictly between initial_ns and ended_ns |
| missed_sample_periods | ヘルパーが返す欠測周期数 | 1 | actual nonnegative integer output |

`missed_periods_before=0` in the first receipt legitimately describes the
pre-callback state. It cannot establish zero missed periods in the terminal
summary. The retained measurement auditor's missed-period gate checks only
whether the final count differs from zero; this diagnostic does not construct
or run its whole task-effect/release gate and makes no full false-PASS claim.
Existing v2 service regressions remain true within their asserted endpoints,
but do not assert this terminal statistic. A future repair needs a specified
terminal-boundary convention and double-counting protection on continuation.

Source pins are in SOURCE.json. The code is retained as `.py.txt` to avoid
automatic discovery. To reconstruct in a new scratch directory, copy these
artifacts, rename probe.py.txt/check_saved.py.txt to `.py`, create `source/`, and
export the three filenames in SOURCE.json using `git show
8f5872874760b671b558a7febe4e14a23261d753:research/doom/NAME.py`. Both helpers also
match this archive's exact sources/fair_v2 copies. Run `python3 -B probe.py`, then
`python3 -B check_saved.py` in that scratch directory; never overwrite retained
raw/receipts. These commands are ordinary construction checks, not permission
to rerun original formal producers.

Injected clock and readiness functions are not real OS timing, stdin pipes,
game/model/controller/release/benefit or a nonreturning bound. No actual 350 ms
latency measurement is claimed. Public receipt derivatives replace absolute
local paths only; PROVENANCE.json maps originals retained privately. stdout,
stderr, plan, raw and checker results remain exact bytes. prior-SHA256SUMS and
the previous immutable Git head preserve the pre-addition manifest.
