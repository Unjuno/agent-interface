# Three-arm target-dispatch → lifecycle → raw-v2 construction

Date: 2026-10-04 JST. This is host-only synthetic construction under #5130, not a live Mindustry or economics result.

## H / T / D / C / U

- **H:** Existing two-target dispatch construction can be composed task-by-task with the fake-mod private lifecycle channel, and the independently implemented raw-v2 auditor can reconstruct both target input/release rows and private reset/geometry witnesses from the joined raw events.
- **T:** Run the frozen 18-task three-arm synthetic route walk; for each task compile and submit the palette point and then the world point using two synthetic fresh-observation callbacks; retain persistent A3→B1 old-reference refusal and repair; join the captured target dispatch evidence to the fake-mod lifecycle and event schedule; audit the resulting raw bytes with raw-v2.
- **D:** Construction passes only if each task has its two ordered admissions and releases, the persistent stale A3 reference is refused before repair with zero admissions, all 18 lifecycle resets and all three A3→B1 geometry transitions reconcile, and raw-v2 returns `PASS_CONSTRUCTION_ONLY` without audit errors.
- **C:** The preregistered task schedule, routing, synthetic observations, compiler/submit callbacks and private-channel fixture are deterministic construction inputs. This does not change the frozen scientific allocation or substitute for a live adapter.
- **U:** All target observations, compiler/submission results, task traces, model calls and reset/game evidence are synthetic. The raw explicitly carries sentinel identities and `source_identity_verified=false`. No live socket payload, Mindustry effect, physical input/release, model behavior, artifact identity, allocation, or economic conclusion is established.

## Retained capture and validation

The first immutable capture is `construction/raw_target_dispatch_lifecycle_20261004_01/`:

- Raw event SHA-256: `cbddc8c0d431f451f85317631db5abcc5193deb525375e869e16d61351b2913a`.
- Raw-v2 result: `PASS_CONSTRUCTION_ONLY`, `errors=[]`, synthetic evaluator `RETAIN`, break-even task 2.
- Lifecycle reconstruction: 18 resets, 3 geometry transitions.
- Source identity: `false`; identities remain synthetic sentinels.
- Focused private-channel tests: 5/5; full package suite: 97/97; inherited decision probe: 10 controls passed; `git diff --check`: passed.
- The branch was based on current main `d22c094a4a2e2292333479573c2eb446c345e1b9` when checked.

The first run command is `python research/integration/mindustry_three_arm_economics_20260928/run_raw_lifecycle_adapter_construction.py raw_target_dispatch_lifecycle_20261004_01`. That capture predates the persisted dispatch-sidecar audit described below and remains unchanged.

### Independent dispatch/raw join control (2026-10-04)

The raw-v2 auditor verifies admission/release joins but does not retain target names or each compiled request's expected observation sequence. The additive `audit_target_dispatch_capture.py` therefore independently joins a retained dispatch sidecar to raw task events. It verifies exactly 18 tasks and 36 ordered palette/world dispatches, each request's expected sequence against a newer raw observation, terminal/released request-ID binding, input feedback/release rows, and the persistent B1 stale-refusal/repair relation. Six tests include five negative mutations: reversed target order, stale request sequence, missing release, an admitted old B1 reference, and malformed raw observation input.

The updated runner writes `target-dispatch-events.json` and `dispatch-audit.json` beside the raw-v2 capture. Its latest immutable output is `construction/raw_target_dispatch_lifecycle_20261004_03/`; the printed disposition is `PASS_CONSTRUCTION_ONLY`, the sidecar audit is `PASS_SYNTHETIC_DISPATCH_JOIN` for 18 tasks/36 dispatches, and source identity remains false. Reproduction command: `python research/integration/mindustry_three_arm_economics_20260928/run_raw_lifecycle_adapter_construction.py raw_target_dispatch_lifecycle_20261004_03`.

The committed `SHA256SUMS` covers all four result files. Raw SHA-256 is `814b5dd83cfe7d963914020db02588a8604548c6e82b4db66493cb88ae1ef8bf`; target-dispatch sidecar SHA-256 is `b3c1eaf0b5093374ee8463cade2217a3197aff938ea968a98e3df7554a48ca66`.

On that source, the dedicated join mutation suite passes 6/6 and the full package suite passes 103/103; inherited decision probe passes with 10 controls. A fresh read-only sidecar audit exactly matches the retained `dispatch-audit.json`. This second audit is a host-side synthetic integrity check, not live evidence or source authentication. All model/game/socket/compiler/reset callbacks remain simulated.

No Docker operation, Actions workflow, Mindustry process, socket, model call, task input, or formal allocation was performed. The #5130 named-slot and sibling-container gate remains active. Actual live adapters and formal results remain open.

## One-attempt socket submit adapter (host construction, 2026-10-04)

The target dispatch callback seam now has an additive implementation in
`target_socket_submit_v1.py`, paired with
`mindustry_three_arm_socket_v2.py`. The adapter sends one compiled request
through the existing v2 Unix-socket protocol, scopes the response by the
command's action ID, requires the bridge's fresh `stdin_flushed` receipt and
exactly one same-ID terminal record, and returns the dispatch contract's
receipt only when `release.verified` is true. It consumes the action before
attempting transport; timeout, rejection, malformed identity, cursor failure,
and unverified release stop without retry. The action ID also serves as the
session-local transport request ID; the frozen six-task route has unique IDs
for all twelve target submissions.

Thirteen focused host tests pass, including wrapper binding and dispatch/compiler
composition, JSON-line wire serialization, non-authorizing response metadata,
lost-response/no-retry, unattributed rejection, wrong action/request identity,
unverified release, replayed or unflushed command receipt, and nonadvancing
cursor controls. The full package passes 116/116. A required trace sink receives
the compiled request before socket exchange, then the full response or an
uncertain-transport event; sink failure before exchange prevents transmission.
The included `JsonlTraceSink` uses exclusive file creation and fsyncs each
record, and its test verifies ordered readback and refusal to overwrite an
existing output. Arbitrary caller-supplied sinks still carry a durability
obligation. These tests inject the exchange response or a fake socket and do
not open an AF_UNIX socket on this Windows host; they verify adapter semantics
and trace persistence behavior, not the actual bridge process, live images,
Mindustry input, or task effects. A read-only
re-audit of the retained capture
still returns `PASS_CONSTRUCTION_ONLY` plus `PASS_SYNTHETIC_DISPATCH_JOIN`
(18 tasks/36 dispatches), with `source_identity_verified=false`; all four
manifest hashes match their current bytes. The wrapper targets the v2 bridge,
but no live socket process or formal allocation was run. The #5130 container
lane remains unassigned, and no Docker command was issued.
