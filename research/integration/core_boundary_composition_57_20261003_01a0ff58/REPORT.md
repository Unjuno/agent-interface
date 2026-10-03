# Retained three-boundary integration check

Worker/session `01a0ff58-7772-7312-9c2a-459f38d6734d`, FINAL-v5, Issue #57.
The I lane was selected because existing reviewed repairs were accumulating
without composition evidence. No new mechanism or shared-runtime edit was
introduced; original author scopes and historical scientific records remain.

## Source and execution

Pinned base `3116528f3abe0fec72cfc1b5b2b5b4b05538512e`, common review base
`11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d`. All fifteen baseline core files
were compared byte-for-byte between those commits. Exact candidate heads:

| Candidate | Head |
|---|---|
| #6860 manifest enum checks | `5821ec3adaa01a44a13011bdf1f069b716441981` |
| #6863 compiled expected-sequence check | `82bf35dba0c709370e18d3ccacef434818879ba5` |
| #6866 current-evidence scalar checks | `abd318643112150d073a242926494145c6461e33` |

Only their `runtime/core_v1` executable/test diffs were applied to a separate
exact source fixture. No original runtime file was edited. `patches/` retains
all three actual Git diffs. Their full evidence/index trees were not combined;
there is no complete-PR integration or main apply candidate. Source IDs and
original Git blob/SHA-256 identities are in SOURCE.json.

Native Windows CPython 3.11.9, AMD64. FREEZE.json records interpreter hash,
platform and exact original source/input/auditor bytes, frozen at
2026-10-03 01:32:09 UTC (10:32:09 JST). Each runner was invoked once, followed
by raw-only audit; command arguments, UTC start/end, runner exit, stdout and
stderr identities are retained under execution/. No physical timing metric
was collected. Each command was sequential; thread environment variables were
one and do not establish OS CPU enforcement or absence of other workloads.

## Input contract and denominator

The independent oracle enumerates exactly the prospective five-dimensional
ordered product in cases.jsonl: 8 manifest profiles, 6 core-time values,
4 current observation values, 4 binding values and 4 compiled sequence values.
Each arm has 3,072 distinct rows; each row records actual core result, actual
compiled callback/journal order, terminal/error and exact typed input hashes.

| Field | 日本語の意味・定義 | SI 単位 | 範囲・前提 | 型 |
|---|---|---|---|---|
| now_ns | core に渡す現在時刻の証拠値。実時計の測定ではない | s（格納は ns） | 正常値は 0..2^63−1。境界 0/100/101 と型違いを検査 | exact Python int、負例は float/bool |
| current_observation_seq | 現在観測の世代番号 | 1（無次元） | 正常値は 0..2^63−1。固定 source 世代 1 と照合 | exact Python int、負例は bool/float |
| current_binding_revision | 現在 binding の改訂番号 | 1（無次元） | 正常値は 0..2^63−1。固定 source 改訂 1 と照合 | exact Python int、負例は bool/float |
| expected_sequence | compiled adapter が返す観測世代番号 | 1（無次元） | 現在 compiled 観測 1 と型・値が一致する場合だけ適格 | exact Python int、負例は bool/float |
| valid_until_ns | compiled admission の期限 | s（格納は ns） | 1,000,000 ns に固定、graph clock は 0。core lease と別契約 | exact Python int |

All graph observations, effect/release returns and clock values are authored
synthetic controls. Core time inputs deliberately test that API's metadata
validation; they are not asserted to be physical wall time. The adapter is
explicit inert test glue, not the public X11/Win32/Quartz path. There is no
claim that the core lease transfers to the separate compiled lease.

## Outcome and independent arithmetic/type reconstruction

Baseline: 3,072 rows, 2,164 oracle mismatch rows, 135 inert execute entries and
135 synthetic completions. Of those entries, 133 violate the declared
valid-input gate. Baseline exceptions: 1,152 TypeError and 45 ValueError;
1,875 rows return a terminal. These are directed authored combinations, not
natural prevalence, a safety rate or physical backend effect.

Combined: 3,072 rows, zero oracle mismatches/evidence errors, two inert execute
entries and two synthetic completions. Both are valid controls: core time
zero and equality at 100 ns. All other inputs either refuse at core with the
expected typed priority or reject at compiled admission before execute.
Original baseline raw SHA-256:
`4f277eb70ee44af906bdf29330e8728f4ac4863228a4e1cbb5f576b5fbc59392`.
Combined raw SHA-256:
`d0d369c30bf6f924bb203a8dd731a5519d8bc0c225f81ffdce737d32c4a90807`.

The separately implemented raw-only auditor imports neither runner nor
runtime. It independently reconstructs frozen inputs/types and row order,
core refusal precedence, expected graph response, exact action/effect counts,
input immutability and release journal evidence. It does not independently
prove that a synthetic adapter corresponds to real application semantics.

Seven one-guard deletions are detected: manifest OS/state/frame 384 mismatch
rows each; core now/observation/binding checks 144 each; compiled sequence
check 4. Seven raw corruptions reject: missing row, duplicate row, removed
execute entry, removed refusal, boolean-to-integer result, internally rehashed
input-type change, and release boolean-to-integer change. The source and all
full raw records for the seven corrected deletion controls are retained;
the two completed first-wrapper controls are also preserved. Gzip decompression
reconciles original raw SHA-256/byte lengths; compression is storage only.

Combined core regressions: 84/84 pass normally and with `-O`; side-effect-free
doctor exits 0. Windows host/interpreter differs from hosted 3.12/foreign
platform checks. No hosted outcome is relabeled as local success.
The unchanged optional #3270 replay test passes 2/2 on this host, without
Docker. Its interpreter/OS differs from the hosted Docker command.

## First failure and publication

Original controls.py stopped at the manifest-frame deletion before launching
that mutant: its LF-only needle did not match the CRLF file produced by Git's
Windows apply path. The first two deletion controls had already run, and their
full raw/source are retained. The first exit 1 and error log remain in
execution/controls/. Baseline/combined runs and auditor were not repeated or
edited. controls_v2.py makes only byte-preserving LF/CRLF needle matching and
is separately pinned by CONTROL_FREEZE_V2.json before execution. Its fourteen
controls are effective. No gate or expected outcome changed.

The first traceback includes a private worker path. Its original bytes are
kept in this worker's private work directory; the public derivative replaces
that prefix. LOG_PUBLICATION.json binds original and published SHA-256 and
byte counts. Original execution receipt log hashes remain original hashes,
with the explicit derivative relation; they do not pretend the redacted log
is byte-identical. All source/raw files remain unchanged and byte-preserved
by the package-local .gitattributes.

CI trigger inventory examined 266 push/PR event blocks. The unconditional
deterministic #3270 replay workflow can run on PR creation. The legacy #4242
opened workflow can be scheduled, but its only formal job requires the exact
different branch `research/native-handle-destroy-generation-a2-20260923`;
that equality is false for this branch. No formal job is requested by this
publication. No workflow was edited, manually dispatched or canceled. This
static inventory is not a hosted execution result. Required GitHub conditions
for an eventual main apply remain to be confirmed at that operation.

The first committed-tree namespace check exited 2 (GIT_COMMAND_FAILED) because
this partial clone had not fetched the two index blobs, while the checker
explicitly disables lazy object fetching. The first stderr/exit is retained
in execution/workspace-base/. Fetching those exact read-only Git blobs before
a separately recorded retry (exit 0, 156 namespaces reachable) repairs only local source closure, not the index
or any research record. The initial engineering failure is not a science FAIL.

## Decision and next boundary

Adopt the scoped composition evidence for review, retaining
PASS_CORE_BOUNDARY_CONJUNCTION_SCOPED. It adds evidence that the three guards
can coexist within this specific sequential bridge. It is not a content vote,
final current-main apply approval, physical release/effect result, task/model
acceptance, performance benefit or closure of #57/#59. Author and committee
identities, exact proposal digests and current-tree conditional application
remain separate. Main advancement during the fixed check did not trigger a
rerun; apply-stage dependency comparison must use its actual current base.

No shared resource lease, input state or main apply lock was acquired. All
owned commands ended; common fleet deadline/N and effective reasoning setting
were not exposed, so none was fabricated or changed. Continue by using this
evidence in nonauthor reviews and resolving the existing content/apply gates.
