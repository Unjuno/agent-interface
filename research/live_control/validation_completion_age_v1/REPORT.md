# Result — validation-completion age (#4010)

**PASS_VALIDATION_COMPLETION_AGE_BOUNDARY_SCOPED.** One preregistered allocation,
three successful seven-case batches, 21/21 cases, zero retries/replacements or
post-freeze source changes. Independent raw-only audit: zero errors; 12/12
semantic corruption controls rejected. All three batch/actor/Xvfb exits are0,
private sockets removed; no model, keyboard/mouse/XTEST or authority.

Source was published before formal batch0 in commit
`6d7d74c9fc14f941f505f50749d801472efe1d03` and read back against Git blob identities.
FREEZE.json SHA256 is `bfaeb2e9da56dc4dbe0443fe01d5446ab5411c431d5bae9025fd9a36d308cdfc`.
The exact first formal audit has6,543 bytes and SHA256
`e34fb4f7b66ea4c4503481144dac2c66a53291d2ed43632f5434176869a4c406`.

## H / T / D / C / U disposition

H confirmed at the declared boundary: receipt-age qualification can expire
while validation runs. The added gate measures age at a later sample without
restamping capture or overriding the original schema/digest/identity refusals.
T completed the seven registered modes three times. Each mode validates one
real native-XGetImage packet once; both policies interpret that same result.
D all21 gates and raw/clock/pixel/source/process checks pass. C the60ms verifier
wait is intentionally injected, not normal hash cost or GIL attribution. U this
is one private fixture, not model/task utility, generic currentness, production
input admission, or population reliability. PLAN.md contains the conditional
analytical proof, variable table, precise schedule and original stop rules.

## Observations

All ages below are milliseconds from native acquisition start; cells show median
[min,max] across exactly3 case repetitions. Environment: supplied Linux x86_64
execution container, Python3.13.5, GCC14.2.0, libX11/Xvfb, glibc2.41, old Xlib0.15,
AMD EPYC9V74 guest CPUs0–4; CPU frequency and host load unpinned. Frame32x32 BGRX,
4096bytes; one packet per case, seven cases per serial batch. No Docker/OrbStack
engine/image attestation. These are delay-injection diagnostics, not a latency
benchmark, speedup or normal-workload distribution.

| Mode | Receipt age ms | Validation-sample age ms | Receipt label -> added gate |
|---|---|---|---|
| PROMPT_VALID |0.116 [0.078,0.209]|0.214 [0.124,0.331]|fresh -> fresh at sample|
| DELAYED_UNCHANGED |0.153 [0.075,0.257]|60.390 [60.267,60.539]|fresh -> stale at sample|
| DELAYED_CHANGED |0.184 [0.177,0.264]|60.432 [60.392,60.482]|fresh -> stale at sample|
| PROMPT_CHANGED |0.196 [0.158,0.199]|0.417 [0.411,0.428]|fresh -> fresh at sample|
| STALE_BEFORE_RECEIPT |60.230 [60.221,60.265]|60.335 [60.329,60.363]|stale -> stale|
| BAD_DIGEST |0.183 [0.152,0.185]|0.236 [0.202,0.240]|invalid -> invalid|
| WRONG_ID |0.138 [0.101,0.142]|0.169 [0.135,0.177]|invalid -> invalid|

Six delayed-validation cases are receipt-fresh but over20ms at the final sample;
all six are refused by the additional gate. Six prompt cases remain qualified.
Three pre-receipt-stale and six invalid controls retain their original refusals.
The three PROMPT_CHANGED captures are less than0.429ms old yet differ from
independent current pixels: a display update occurred during validation. This
is an explicit counterexample to treating a small age as unchanged semantic
state. It is not a failure of the age-only candidate contract.

## Preservation and construction

The previous receive/hash factorial remains STOP_CONTAINER_TOOL_TIMEOUT and
HOLD_EVIDENCE_INCOMPLETE, 13/32 complete cases. It is not resumed, pooled, or
upgraded. Its complete prior ZIP remains a conversation attachment (2,966,309
bytes, SHA256 25d1de4ba0a2f6e8e049c645d4b6bc06fd00de0354fd9f763b3f6d3b6ff5fbd2).
This GitHub bundle retains its report/freeze/HOLD and selected posthoc packets,
not all3,420 old received packets. POSTHOC_BOUNDARY.json preserves an initial
incorrect empty-inventory read; POSTHOC_BOUNDARY_V2.json fixes that read without
changing any predecessor bytes. Three selected receipt-fresh/post-validation-
stale observations motivated this new endpoint; they are not a failure-rate
estimate or retroactive violation of the old receipt-time label.

Construction01 failed at a copied-source subpath before X11. Construction02
failed at old-Xlib Xauthority-family matching. Construction03 failed at old-Xlib
str/bytes conversion. Their outputs and the two failed runner versions remain
in the archive, with0 cases each. Construction04 completed7 excluded cases;
12 unit tests and12 corruption controls passed before formal freeze. The final
source was fixed only before the published freeze. No formal result was tuned.

## Reconstruct without executing the experiment

The lossless evidence tar.xz is split into four binary fragments solely for MCP
transport. ARCHIVE.json binds their order, each SHA256 and the concatenated
25,164-byte archive SHA256
`6190e6774af53e4987f13a74f14f40ec895cc2a98a658fab2061446c2cea5b79`.
It contains84 files /777,404 member bytes: all new raw cases, process/wire/pixel
records, actual batch waits, original audit, construction incidents, tests,
and predecessor receipts/exemplars. Source is separate and readable.

From this directory use a NEW destination:
```
python -B unpack_evidence.py /tmp/validation-age-audit-4010
cd /tmp/validation-age-audit-4010
python -B audit.py formal-01 --controls
python -B -m unittest test_contract -v
```
The decoder verifies every part and the archive, refuses overwrite/path traversal
and nonordinary members, and copies exact frozen source. Native.so is only
decompressed and hashed for this audit, never loaded. No Xvfb, GUI or allocation
is launched by these commands. Do not use Python -O: auditor assertions are
required. Do not run execute.py against the consumed allocation.

Local restoration to a fresh directory verified all84 member hashes; its raw
formal audit was byte-identical to the first audit, and all12 unit tests passed.
This is artifact revalidation, not another experiment or independent human review.

## Integration handoff and remaining roadmap

Keep receipt-time age and post-validation sample age as separate named fields.
Bind each to the original acquisition interval, session/identity and clock domain.
Do not translate FRESH_AT_VALIDATION_SAMPLE into current target authority, model
consumption, or later-use freshness. The old label was not a production bug;
no shared runtime code is changed here.

Completed: source/lineage audit, construction, public freeze, 21-case allocation,
raw reconstruction and lossless-restoration check. PR acceptance/main readback
remain the publication gates. Broader #2117 and #2789 model/application/desktop
acceptance and the repository-wide ROADMAP remain open. A future integration
must identify the actual production consumption point and evaluate its freshness
and task effect; this study alone does not authorize an extra runtime mechanism.

Related transfer areas: distributed message consumers (receipt versus processing
age), computer vision (recent pixels versus current scene), and control systems
(observation qualification versus actuation authority). These are engineering
implications, not separately measured transfer results.
