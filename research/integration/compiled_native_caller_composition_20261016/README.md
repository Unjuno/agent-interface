# Caller v3 through NativeHandleBridge with Fake X transport

2026-10-16 JST. Main base `4c3839cb5160fbb238b52c5f1574f5d2343c3063`;
tested code `76906e61ae9e1d4963e4484214ea003ac32127ed`.
Decision: **RETAIN_FAKE_X_CALLER_NATIVE_BRIDGE_COMPOSITION**.
No production behavior is changed. The regression is registered once in harness.

## Connection exercised

Actual adaptive caller v3 → explicit compiled execution v2 → final-target builder
→ exact-value form compiler → graph → guarded `_Adapter` → real handle store,
NativeHandleBridge, guarded backend and runtime session. The builder maps the
promoted `final_field` / `final_submit` aliases; cached `old_*` aliases are never
minted. Handles are minted from retained captures and re-resolved by the actual
store. Native input methods execute guarded keyboard chords and retain receipts.

The existing FakeX fixture replaces backend construction/platform setup,
capture transport, XTest emission, keymap and process identity reads. An explicit
synthetic RGB pixel outside both target patches advances after the fake chord.
Read-only perception and effect callbacks recognize that synthetic phase; this
is neither a real text-entry recipe nor independent application scoring. Static
target patches remain intact so generation controls are not texture failures.
No display connection, real input, model, provider, WSL/container or allocation
was used. Warm reuse has zero model calls by construction, not measured savings.

## Eight retained rows per mode

| Condition | Fake emissions / completed prefix | Outer result |
|---|---|---|
| Final target, outer effect unavailable | Two complete CTRL+a chords / 2 | TASK_NOT_VERIFIED |
| Final target, outer effect failed | Two complete chords / 2 | TASK_NOT_VERIFIED |
| Process generation changed before entry | None / 0 | EXECUTION_INCOMPLETE |
| Generation changed after first CTRL press | CTRL press and release only / 0 | EXECUTION_INCOMPLETE |
| Generation changed by first effect callback | One complete chord / 1 | EXECUTION_INCOMPLETE |
| Wrong value after entry | One complete chord / 1 | EXECUTION_INCOMPLETE |
| Unknown value after entry | One complete chord / 1 | EXECUTION_INCOMPLETE |
| Receipt sink fails after both actions | Two complete chords / 2 | CALLER_FAILED |

No row leaves a fake key down or a pending adapter authorization. Completed
native input terminals retain verified synthetic readback. In the between-action
case, guarded admission can use the prior retained observation, but the actual
bridge checks the new generation and refuses Submit before input. That refusal
has `input_dispatched=False` and `release.verified=False`; it does not manufacture
a new release receipt. The first chord's verified completion remains the prefix.
No outer verifier runs on incomplete execution or sink failure. Nothing retries.

## Verification and preserved construction failure

Final normal and actual optimized Python: **54 modules / 374 unique methods**,
zero failures/errors/skips, including these eight methods. Selected source/data
pins number 91 with separate Git/worktree byte hashes and semantic joins. These
are selected joins, not a complete dependency closure or all-platform suite.
CONDITIONS' base is the tested code; inherited old_prs is historical navigation.

The pinned pre-repair compiler from `04e2602e...` runs with the final eight-method
probe and fails **seven assertions, zero errors**, in each mode. All its fake
emission lists are empty: its contradictory entry dependency still prevents
native execution. This is the complete original module, not a mocked return.

The first broad construction at `d5b3ca2875...` failed one assertion in each
374-method mode. The probe had incorrectly required verified release even for a
pre-input refusal. `construction-r3-*` preserves complete logs, conditions,
source joins and raw records. The corrected probe explicitly checks the
False/False refusal while retaining the earlier verified prefix. Earlier local
fixture setup errors (existing output directory; nonzero initial marker) were
corrected before that source-pinned broad run; they are not runtime findings.

Six deterministic gzip archives retain complete ROWS/RECORDS, including bridge
files as exact hex bytes before close, native observation artifacts and receipts.
Uncompressed checks are in [RECORD_ARCHIVES.json](RECORD_ARCHIVES.json).
A saved-only reader checks caller/core/terminal/execution/reference joins and
all eight emission/prefix/effect outcomes. Six copied contradictions are rejected
per reader mode: hidden input, lost prefix, false task success, wrong selected
target, false release and dropped raw. It imports neither candidate nor scorer.
The `.py.txt` tools are inert references with their original local path bindings.

## Remaining qualification

This closes a missing local composition check beyond the earlier memory Bridge
fixture. Real XRes/process/window evidence, stalled native transport, physical
release timing, semantic value recognition, collateral effects, independent
task scoring, bounded semantic recovery and matched/second-domain economics
remain open. It does not qualify the public MCP end-to-end route or a live model
route; this caller is the explicit research v3 helper. Keep #17/#59/#57 open.
Next qualify actual domain grounding/perception/effect adapters and a bounded
recovery decision using these same caller/bridge boundaries; do not reuse the
synthetic phase as application success or rerun consumed historical allocations.
