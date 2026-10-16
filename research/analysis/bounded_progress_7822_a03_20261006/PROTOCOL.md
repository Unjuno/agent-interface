# #7822 A03: controllability-closed finite cross-check

Allocation: BP-7822-LINUX-A03-20261006. Intake main a3e6b0c1ab8d6af5c24abb88a451ce41c4ede028.
Subject: byte-identical candidate.py from A02 PR #8228, head 7c6f599cf250e7991f2115ccc5911d26cf53e7cb, Git blob 32f363f8dac04b66fb02eb65d91901ac03c0cfef. The file is vendored as candidate_a02.py. Neither A01 nor A02 is rerun or changed. This is an additional method test, not a new solver or production promotion. Original repository license: Apache-2.0.

## H/T/D/C/U and road map

H: The unchanged finite-horizon solver agrees with an independent stationary-policy enumeration and cycle/longest-path oracle. Separately, its filtered-graph nonblocking diagnostic need not equal existence of an implementable safe/evidenced nonblocking supervisor. Removing an uncontrollable bad edge is not an available supervisor operation. Conversely, including all optional controllable edges can add avoidable dead ends. These diagnostic distinctions do not by themselves falsify the solver.

T: One candidate process generates and scores 2,405 new public graphs. Four slots q0->q0, q0->q1, q1->q0, q1->g each have seven possibilities: absent; safe/evidenced C; safe/evidenced U; unsafe C; unsafe U; safe/evidence-missing C; safe/evidence-missing U. itertools lexicographic order gives 2,401 graphs. Four controls add initial goal, direct goal, three-step path and optional controllable dead end. Horizon cap is three events. Every goal is terminal. Candidate receives only each declared public graph, not oracle outputs. All graph bytes and full returned policy layers are retained in lossless RAW.jsonl.xz. The auditor reconstructs corpus membership by independent base-seven arithmetic, never importing generator, runner or candidate.

D: Require all 2,405 ordered records, exact subject/source identity, actual zero role exits, exact minimal bounded-policy status and layers on every graph, no action/completion claims, and 12 effective well-formed output mutations rejected. Each mutation must change bytes, pass on the original row, and fail normally on the changed row. Solver mismatch is FAIL; missing role/source/denominator evidence is HOLD/STOP. Report all filtered-diagnostic versus implementable-supervisor differences with explicit witnesses; no population rate or user-benefit inference. No threshold is selected from formal results.

C: Fully observed finite games; unique edge/event IDs; honest complete graph and declared evidence flags; arbitrary adversarial choice among enabled edges; no fairness; terminal stopping at a marker. A graph predicate is not evidence of a GUI effect. The independent oracle shares this stipulated mathematical contract, not candidate code. The audit is separately implemented by the same author, not independent human review. Filters are legitimate graph projections when labelled as such; only interpreting them as achievable control is challenged.

U: No partial observation, unknown transitions, learned markers, real models, GUI/input, effect, wall-clock deadline, release safety, latency/token benefit or general reliability. Supplied Linux x86_64 container / CPython 3.13.5 / stdlib only. No Docker/OrbStack/WSLc CLI or pinned image attestation is available in this session. This local supplied-container method allocation is explicitly chosen before execution, not a fallback rerun of another protocol. No shared Engine, GPU, host-workstation mutation, installs, experiment network or user data. Diagnostic host monotonic nanoseconds are not calibrated timing measurements; no combined uncertainty or coverage factor is fabricated.

Road map: read ownership and preserve old studies -> excluded construction -> public complete source/freeze readback -> candidate once -> auditor once only after candidate exit zero -> retain full output, mutations and failures -> additive evidence PR -> exact-head CI and review -> merge only when qualified. Consumed role markers prevent original role reruns. Read-only re-audit is allowed and does not regenerate candidate observations. All work stays in this namespace; no existing runtime/workflow/index is edited.

## Independent oracle and completeness argument

For a fixed graph, enumerate every subset of controllable edges and retain every uncontrollable edge. This enumerates every stationary edge-enabling policy. For each policy, start from the queried state and traverse enabled edges, stopping at goals. Reject the policy if any reachable enabled edge is unsafe or lacks evidence. For ordinary nonblocking, independently search for a goal path from every reachable state. This allows infinite cycles: it is a possibility-of-completion condition, not all-path termination.

For bounded progress, additionally reject any reachable non-goal cycle or non-goal dead end. In a finite graph with no reachable non-goal cycle, every permitted run terminates at a goal. Recursively enumerate its path lengths; their maximum is that policy's exact worst-case event count. Minimize this maximum over all policies. This computation uses no finite-horizon winning-set recurrence.

Why stationary enumeration is sufficient here: assume some history-dependent policy forces a goal in finitely many transitions from a state. Associate each winning state with its least achievable worst-case remaining count. A non-goal winning state cannot enable an uncontrollable transition to a state with equal or larger count, since the environment could choose it and violate the purported minimum. At least one enabled edge must exist; a needed controllable choice can similarly be selected with strictly smaller count. Select these decreasing controllable choices once per state and retain every uncontrollable edge. This constructs a stationary policy with a strictly decreasing nonnegative count until a goal. Conversely every enumerated stationary policy is an allowed history-dependent policy. Thus the minima coincide for this fully observed finite reachability contract. Fairness, probabilistic scheduling and wall-clock bounds are not used.

The auditor repeats the stationary oracle from every state, reconstructs all returned horizon-layer state sets and all permitted edges, and checks exact canonical bytes for policy structure. It separately checks strict JSON integer/Boolean types so True cannot substitute for an integer bound or ordinal.

## Variable / unit table

| Symbol | Meaning (Japanese) | SI unit | Definition | Domain / assumptions | Type |
|---|---|---|---|---|---|
| q0,q1,q2,d,g | 初期・中間・行き止まり・目標状態の識別子 | 1 | Named graph states; g is terminal | Finite, fully observed | categorical scalar |
| C,U | 制御可能・制御不能イベント | 1 | Only C edges may be disabled | Two distinct categories | categorical scalar |
| h | 残り遷移数 | 1 (event count) | Number of permitted transitions before goal | Nonnegative integer, cap 3 in this corpus | integer scalar |
| N | 全グラフ数 | 1 | 2,401 grid graphs plus four directed controls | Fixed at 2,405 | integer scalar |
| E | 遷移の集合 | 1 | Explicit source,target,kind,safe,evidence tuples | Finite, unique IDs | finite set |
| S | 有効化する制御可能遷移部分集合 | 1 | One enumerated stationary policy; all U always retained | Subset of C edges | finite set |
| bound | 最小の最悪時遷移数 | 1 | Minimum over complete compliant acyclic policies | Integer or null when not achievable within cap | optional integer |

Unit check: path length and h both count events; decrementing h per edge is dimensionally consistent. No event count is converted to seconds. Supervisor timestamps are nanoseconds in one host clock domain only.

## Prior art

Jiao, Zhang & Cai, arXiv:2103.08133 (2021), distinguishes finite nonblockingness and infinite livelock; this study does not reproduce their synthesis theorem. Zhang et al., Automatica 170 (2024), 111879, DOI 10.1016/j.automatica.2024.111879, studies quantitative nonblockingness. Both precede this finite implementation check. Neither establishes real GUI marker evidence or runtime guarantees here.

## Execution commands

From this directory: python -S -B invoke.py candidate; only after zero exit, python -S -B invoke.py auditor. Each role has a 30-second subprocess limit inside a 45-second tool invocation. Tests: python -S -B -m unittest -v test_oracle. Four disjoint subject construction graphs and ten oracle tests precede the freeze. The initial intentionally incomplete oracle produced seven expected assertion failures; that source and red/green logs are retained in construction/.
