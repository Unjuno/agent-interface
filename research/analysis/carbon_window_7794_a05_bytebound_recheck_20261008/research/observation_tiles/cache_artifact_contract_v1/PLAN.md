# #4029: cache maintenance versus encoded and pixel identity

## H — new support envelope, not an old contract failure

The original IMAGE_ARTIFACT.md explicitly excludes externally edited cached PNGs.
Keep its replay PASS and timings unchanged. This study asks whether the existing
sink can be composed with cooperative, completed storage maintenance. It is not
#3932's concurrent FFmpeg publication race or #3978/#3995's FD experiments.

ORIGINAL uses unchanged Frame plus path existence. BYTE_PIN_REPAIR compares the
encoded SHA256 saved at successful creation. PIXEL_CHECK_REPAIR verifies and
fully decodes the same bounded PNG bytes, comparing mode, geometry and all
sample bytes. Either wrapper invalidates its own previous-frame cache on failed
validation, then delegates to the exact existing sink's exclusive new-file
creation. No production source edit or overwriting of old evidence is allowed.

H: both wrappers recover exact images under quiescent maintenance; only the
pixel guard retains reuse for a different lossless PNG representation. Original
output can violate this expanded contract without violating its original one.

## T — prospective finite test

Exactly two first-outcome batches, batch0(rep0) then batch1(rep1), each eight
scenarios x three policies =24. Forty-eight fresh trial processes and42 separate
read-only byte collectors total. Every case starts a new96x64 RGB sink. Formal
rep0/1 is disjoint from construction rep100. Order is repetition, scenario,
policy as explicitly listed in PLAN.json. No random frequency or population
claim. All commands and stdout/stderr/actual exits remain raw evidence.

Scenarios: unchanged; changed frame; missing cache;33-byte truncated PNG; other
pixels/same dimensions;48x128 geometry/same raw length; identical pixels encoded
at compression0 with a tEXt note; occupied next002.png with a changed frame.
All maintenance completes BEFORE the second publish and consumer read. No
concurrent access is tested. The candidate never receives a scenario label.

Provided Linux x86_64/CPython3.13.5/Pillow12.3.0 container, exact versions and
binary/module hashes in ENVIRONMENT.json. No Docker/OrbStack image attestation,
package install, model/provider, GUI/input, network experiment, user document or
shared runtime. Child env is sanitized. Regular cooperative files only.

Batch subprocess deadline30s; each trial/consumer3s. Exclusive output and start
markers prevent rerun. Batch1 requires complete zero-exit batch0 with matching
raw digest. Missing/failed batch ends the allocation with no pooling/replacement.
An invocation never runs both batches inside one external tool call.

Independent audit implements RGB8/noninterlaced PNG CRC, deflate and filters in
stdlib, imports no Pillow or candidate, reconstructs every original/current
frame from the frozen generator, checks actual retained disk bytes and collector
bytes, and checks process/source/authority identities. It is independent code
and process by the same author, not independent human review.

## D — exact finite gates

PASS_CACHE_MAINTENANCE_CONTRACT_SCOPED requires all48 cases/two batch exits/source
and raw bindings; original has six wrong/invalid outputs (truncation/pixels/
geometry), both wrappers have14/14 exact noncollision outputs each, every arm
regenerates missing cache and changed frames, unchanged reuses, byte guard
regenerates two lossless reencodings while pixel guard and original reuse them,
and all six occupied names refuse without changing sentinel bytes. Every12
copied-raw semantic/type/process/source corruption challenges must reject in
each formal batch. Audit integrity does not rescue unsafe original comparator
results under the expanded contract. Complete disagreement is scientific FAIL;
source/process/incomplete evidence is HOLD/STOP. No timing adoption gate.

## Conditional argument (analysis before experiment)

1. Assume a successful first publication encoded its requested immutable frame.
2. Original reuse compares only that frame and file existence; maintenance can
   preserve existence while changing or truncating bytes. Its predicate alone
   therefore cannot imply the new decoded-pixel requirement.
3. Under the tested noncolliding byte identities and quiescence, a cached file
   matching the pinned digest is the unchanged previously encoded object. Any
   changed digest triggers fresh encoding. SHA256 is not an authenticity proof
   or mathematical proof of collision freedom over arbitrary inputs.
4. A successful verified full decode equal in dimensions, mode and every sample
   to the current frame directly satisfies the pixel requirement. Otherwise,
   fresh encoding is required. A subsequent collector still needs the no-writer
   assumption; a pre-check cannot guard arbitrary future mutation.
5. Two PNG byte strings may encode identical samples. A byte guard can regenerate
   unnecessarily relative to the pixel criterion; this is extra work, not a
   measured latency penalty. The experiment checks the actual codec and file
   behavior left by these assumptions, rather than claiming a new cache theorem.
6. Exclusive new-file creation rejects an occupied next name. A refusal is not
   proof that an image became available; retained sentinel bytes verify no
   overwrite only at this bounded fixture boundary.

## Fields / units / domains

| Field | Meaning (日本語) | SI/unit | Definition | Domain/assumption | Type |
|---|---|---|---|---|---|
| width,height | 画像寸法 | 1 (pixel count) | Frame dimensions |96,64; geometry control48,128| integer scalar |
| pixels | RGB標本 |1 (byte sequence)|row-major R,G,B,8bit/channel|immutable bytes,3 samples/pixel|byte vector|
| rep |反復識別子|1|formal0/1,construction100|not random sampling|integer scalar|
| image_reused |再利用判定|1|unchanged sink receipt|true/false|Boolean|
| pin |初回PNGバイトのハッシュ|1|SHA256 of created PNG|integrity,not authentication|string|
| image_prepare_ns |元sink内部の準備時間|s (stored ns)|upstream ready minus start|excludes wrapper validation;diagnostic|integer scalar|
| *_ns |プロセス時点|s (stored ns)|same-container perf_counter_ns|software clock,not physical scanout|integer scalar|
| returncode |実プロセス終了値|1|subprocess wait result|integer0 required;Boolean invalid|integer scalar|

Unit check:96 x64 x3 =18,432 sample bytes, not elapsed seconds or model tokens.
All comparisons use bytes/counts; stored nanoseconds are never interpreted as
clock-independent freshness or a task-performance measurement. No calibrated
combined uncertainty or coverage factor is available or required for exact
categorical gates.

## C / U / scope

Output-directory ownership is the changed support assumption. No live GUI/model
presentation, target/epoch/freshness, ACK, authority, disk failure, symlink/FIFO,
hostile file, concurrent write, crash durability, color-profile interpretation,
animation, RGBA/palette or production throughput is tested. Only RGB sample
identity with no color-management metadata applies. Original source and all
prior raw remain immutable. Publication incidents stay in this Issue.

Related disciplines: cache coherence (explicit invalidation), image coding
(lossless byte/sample distinction), interface verification (returned artifacts
versus actual consumer bytes). These are transfer constraints, not deployed
features or broad reliability evidence.

## Sources and roadmap

Pinned source commit1f798cbb60b929e738c6bf8a5912470b38b45ff4; exact full source
blobs in FREEZE.json. Primary external specifications consulted2026-09-22:
https://www.w3.org/TR/png-3/ (sections5,9,11),
https://pillow.readthedocs.io/en/stable/reference/Image.html (open/verify/load),
https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#png .

Source/contract check -> excluded construction -> public freeze -> two batches
-> raw-only audit/corruptions -> full readable source and lossless evidence PR
-> exact-head review/checks and main readback -> only owned safe cleanup.
Concrete #2789 constraint: either keep exclusive artifact ownership or declare
and validate maintenance semantics before reusing images. No runtime adoption
or global ROADMAP completion follows from this study.
