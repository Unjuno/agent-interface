# #6695 A01: preparation/edit-cost and deadline frontier

Worker/session: 01a0ff52-b64b-71d2-b2d6-19a57b40283f. FINAL-v5.
Allocation: REVERSIBILITY-DEADLINE-6695-A01-20261003-01a0ff52.
Parent: https://github.com/Unjuno/agent-interface/issues/6695

This is a new finite synthetic discriminator. The earlier #6707/#6709 12-row PASS, which used zero-duration preparation/correction and universally feasible deadlines, stays unchanged. #5428 utility thresholds and mode switching are separate. No historical allocation is repeated or pooled.

H: overlap between reversible preparation and waiting for an informative signal can improve correct on-time commits relative to WAIT_THEN_PREPARE, but correction cost can erase or reverse the advantage. Exact deadline enforcement must refuse every late irreversible effect. This tests the incremental preparation mechanism, not whether more information helps.

T: exhaustive Cartesian grid: preparation 0,1,2 ms; signal arrival 0,1,2,3 ms; correction 0,1,2 ms; deadline 0..7 ms; scorer truth A/B; informative or UNKNOWN signal; correction route present/absent. Proposal A, commit duration 1 ms. 2,304 schedules, 3 policies, 6,912 rows, one deterministic candidate invocation and one separate raw-only auditor only after exit 0; no retries. Construction uses private small controls, not this formal denominator.

IMMEDIATE starts reversible preparation at zero and commits at earliest readiness without using the signal (diagnostic only). WAIT_THEN_PREPARE waits for the exact same signal, selects that target when informative, then prepares and commits. STAGE_THEN_CORRECT prepares proposal A at zero, waits for both preparation and the same signal, corrects to B only if the reversible route exists, then commits. Signal acquisition is an authored external stream at the same fixed time; no extra observation or information is granted to staging versus waiting. Absent correction cannot modify an existing prepared target, whereas waiting may initially prepare the correct target. Preparations/corrections are benign modeled work with zero irreversible side effects. They may finish beyond the effect deadline; the deadline constrains only the irreversible commit and is checked at commit completion. Refusal has no application effect. No compensating operation is silently treated as undo.

D: PASS_METHOD_SCOPED iff every event/row equals an independent algebraic oracle, every scheduled ID/arm is accounted once, every deadline equality admits and one-ms-short control refuses as specified, no unavailable/UNKNOWN correction changes A, at least one informative/correctable B schedule witnesses each direction of the staged-vs-waiting on-time difference, and seven construction mutations are rejected. Otherwise FAIL_METHOD, or typed infrastructure STOP before execution. This is a discrimination gate, not a universal staging/H-policy win. Exact formal outcome and raw bytes remain immutable.

C: benefit may be ordinary overlap rather than reversibility; a simple wait-before-prepare policy may win when edit cost is high. IMMEDIATE is not an optimized fresh-evidence policy. State/content-specific setup and correction costs are declared, not calibrated. The matched WAIT comparison, not IMMEDIATE, decides the incremental question.

U: authored deterministic times and targets, no actual latency samples/distribution/error bars, GUI, model, task effects, OS input, user data, token or human-tempo measurement. Neither safety nor general optimal policy is established. No real backend/lease authority comes from this model. Scorer truth is mounted only in the auditor container; candidate cannot read it through its admitted mounts. Full offered IDs remain in the denominator.

For informative B with a correction route, staged readiness is max(p,s)+e+c and waiting readiness is s+p+c. Their difference is e-min(p,s). This is derived by subtracting common c and using max(p,s)+min(p,s)=p+s. Staging can be strictly better, equal, or worse. A correct on-time commit additionally requires readiness <= d; no probabilities are estimated.

| Symbol | 日本語の意味・定義 | SI単位 | 範囲・前提 | 型 |
|---|---|---|---|---|
| p | 可逆な初期準備の時間 | s (JSONはms、1ms=0.001s) | 0,1,2ms | 非負整数スカラー |
| s | 共通の観測信号が到着する時刻 | s (JSONはms) | 0,1,2,3ms、同一時計原点 | 非負整数スカラー |
| e | 準備済み内容を訂正する時間 | s (JSONはms) | 0,1,2ms、訂正経路がある場合 | 非負整数スカラー |
| c | 不可逆なcommit完了までの時間 | s (JSONはms) | 固定1ms | 正整数スカラー |
| d | 不可逆効果の完了締切 | s (JSONはms) | 0..7ms、等号を許容 | 非負整数スカラー |
| A,B | 提案/正しい対象のモデル識別子 | 非物理識別子 | 二値、個人情報を含まない | 文字列 |

Runtime is frozen only after a working private-Docker construction check. Requested container limits: 1 CPU, 256MiB, no swap, network none, read-only root/source, bounded PIDs. Record cgroup readbacks; these do not certify host-wide guarantees. Formal output cap 10MiB. Segment cap 45 minutes from initial intake; common fleet deadline is still unconfirmed and is not extended or assigned here.
