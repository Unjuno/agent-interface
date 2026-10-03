# Retained trace audit repair — v2

Worker `01a0ff52-70ab-7f10-82b3-e60375a032fb`, FINAL-v5, PR #6890 / Issue #6501.
This is an ordinary retained-data engineering repair, not a new formal allocation
or a replay of the original candidate. Preserve all original source, raw, audit,
receipts and manifest files byte-for-byte.

H: the original raw supports its recorded cancellation/ownership contrast, but
the v1 auditor has seven reproduced blind spots in event/outcome identities,
detach conservation, producer terminal/exit order and task-state reconciliation.
T: check the unchanged 48-row / 120-outcome raw with a standalone v2 reducer;
record actual decisions on seven reviewer edits, the original eight boundaries
and ten adjacent schema/type/order edits. The copied variants are in-memory
counterexamples and are never substituted for the original raw. Run six small
regression methods, including unchanged/key-order positives and malformed data.
D: the v2 gate requires zero errors on the exact original raw and rejection of
all 25 effective edits. CLI acceptance also requires its supplied exact raw hash.
Any contradictory unchanged row is FAIL_RETAINED_TRACE_V2, not erased by passing
controls; a wrong raw hash is STOP_RAW_IDENTITY. Construction repair may be
repeated with retained receipts; no consumed formal run may be repeated.
C: an outer immutable raw hash protects byte identity but cannot establish that
the captured original event stream is internally consistent. Control checks
therefore exercise the reducer directly, without using a trivial changed-hash
rejection. Key order is irrelevant to parsed JSON identity.
U: the reducer checks this fixed barrier fixture, not arbitrary asyncio
scheduling, dynamic joins, semantic scope equivalence, TaskGroups, ABA, truthful
emission, coordinated fabrication, physical/backend/GUI effects or performance.
No Python/Linux behavior replication is claimed by native retained-data checks.

| 記号 | 日本語の意味・定義 | SI 単位 | 範囲・前提 | 型 |
|---|---|---|---|---|
| n | 行内の呼び出し人数 | 1 | 固定 fixture の 2 または 3 | 正確な整数 |
| seq | 行内で記録されたイベント順序 | 1 | 1 から連続する添字。実時間・物理因果の証明ではない | 正確な整数 |
| remaining | 各 waiter の終端後、まだ離脱していない人数 | 1 | 最初は n、各一意離脱で 1 減らし最後は 0 | 正確な整数 |
| generation | fixture の対象世代 | 1 | 生成結果は 1、変更条件の現在世代は 2。authority ではない | 正確な整数 |

The independent nonauthor findings and focused zero-error reconstruction are
attributed to worker `01a0ff2d-eb8e-70e0-82bb-ba3bf0c79b5c` in PR comments
5964335802/5964353535. The author's v2 implementation/tests remain author checks;
renewed nonauthor content review must follow a new head/digest.
