# #5260 A06 receipt-visibility phase construction

H: The same old-stamp age failure can arise from controlled pre-publication
delay or pre-read delay. Retained write/fsync/replace/read intervals separate
the phases; a final receipt_expired label alone does not identify one.
This does not explain A05's historical row009 or license relaxed freshness.

T: New no-GUI/no-input construction01, eight fresh writers: HOST_BIND and
CONTAINER_TMP x PUBLISH_DELAY100ms and READER_DELAY100ms x idle/cpu_busy.
Seed52606026. Tiny immutable token receipt, timestamp before publication;
first print records stamp/PID/token, then publish once with atomic replace.
Reader records every failed/successful open/parse with before/after clocks,
500ms deadline/poll1ms, no retry of a writer. Busy own-child300ms. Once
candidate/eight writers, once separate readonly auditor; no formal typing.

D: METHOD_PASS_CONSTRUCTION_ONLY if all source/image/fixture/file/PID/phase/
clock/argv/stream identities and clean own-child exits pass; induced delayed
phase must be at least100ms and every first-read payload hash must bind the
one writer trace. H_PASS_BOUNDARY_CONSTRUCTION_ONLY if oldstamp50ms age
fails in both phase arms while full trace retains their distinct phase.
Other outcomes remain H_FAIL/STOP, never replaced or silently rerun.

C: Same cached WSLc Python image217851fe68e7, networknone/sourceRO,
uid65534/requestCPU0.5/512M only, own bind outputs and private/tmp directories.
No GUI/XTest/key/Save/focus manipulation/model/GPU/physical user display.
Independent auditor imports neither candidate nor writer implementation.

U: Artificial100ms delays and filesystem endpoints are construction, not
focus freshness, performance, OOM, Docker parity, public sensor efficacy or
causal attribution to A05. Fresh timestamps at publication/read do not prove
a target remains valid; later focus revalidation still matters. No defaults,
runtime/config/shared service or other-owner allocation changed.

Roadmap: TDD typed phase/file trace gates -> frozen writer/reader/auditor/
fixture/argv/source hash and scoped CPU record -> one8-row construction ->
first raw/streams/independent audit -> readonly controls/additive PR delivery.
Status: preparation only; A05 and earlier allocations remain immutable.
