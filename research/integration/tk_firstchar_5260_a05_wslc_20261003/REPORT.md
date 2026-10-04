# #5260 A05 first construction outcome

**METHOD_PASS_CONSTRUCTION_ONLY**, errors[], but
**H_FAIL_FINITE_FIXTURE_ONLY** under the prospective all-four ACK target gate.

| Arm | N | Admitted | Exacthxy/emptydecoy | Refused with no Key/Save |
| --- | --- | --- | --- | --- |
| NOW_TARGET |4|4|0/4|0|
| ACK_TARGET |4|3|3/4|1|
| ACK_WRONG_TARGET |2|0|0/2|2|

Every NOW row savedxy withh in decoy. The three admitted ACK rows savedhxy
with emptydecoy and no recorded targetFocusOut before first key. Both wrong
clicks refused keys and Save. A fourth ACK target row, index009/cpu_busy,
also refused all key/Save rather than completing the task. This finite
construction does not establish population benefit or a general sensor.

One fresh construction01, ten fresh app PIDs/all exit0, source frozen at
`4cec7d7153f5e91879e87047904b7cb863952535`, MCP FREEZE readback MATCH before
input. All15 frozen source/plan/test hashes remain unchanged. Candidate once
2026-10-03T15:11:43.316880+00:00–2026-10-03T15:12:03.913035+00:00,
exit0/20.5956s; separate raw/file auditor once
2026-10-03T15:12:21.073962+00:00–2026-10-03T15:12:21.638261+00:00,
exit0/0.5640s. These invocation wall times are not a performance comparison.
No retries, replaced rows, post-input source repair or old allocation replay.

## Refusal diagnosis and unresolved visibility boundary

Row009 ready18270325684ns; click18290917912ns; sync18291242140ns;
targetFocusIn18303099346ns; app ack timestamp18315888056ns;
poll start18291247448ns; final refusal18793247003ns. The final guard error
is `receipt_expired`; final focus-state receipt remains target/sequence3.
Thus a target FocusIn existed, but was not admitted by this frozen gate.
No KeyPress/Save request was sent in that row.

The frozen app stamps `written_ns` **before** serializing, flushing, fsyncing
and replacing focus_ack.json. It is not a publication-completed timestamp.
The frozen candidate keeps only the final invalid poll error, not each first
read/parse/seen age. Publication/read latency versus first-observation age
cannot be causally separated from this record. Do not promote a longer
defaultwait or simply relax freshness from these four examples. A fresh
successor can instrument publish/read/admission boundaries separately;
this consumed source/result must remain unchanged.

## Custody and safe controls

The independent auditor imports neither candidate nor focus admission code.
It reconstructs schedule, app/ready/file/PID/token/geometry, acknowledged
FocusIn identity, gate clocks, input requests, frame hashes/byte sizes,
worker/Xvfb/Openbox exits and wrong-target no-input controls.
Single-epoch readiness passes10/10; candidates/raw/audit stream receipts
retain exact argv, hashes and source commit. Images are byte-bound only;
no OCR/useful-visual endpoint is qualified.

35 source/capture/admission/focus tests passed before input. Three new readonly
packet tests were RED for missing verifier, then GREEN;38 current tests pass.
18 corrupt raw copies are rejected by retained audit; originals never changed.
Retained verification invokes zero GUI/input/container commands. Packaging
PASS preserves the scientific H_FAIL, not an efficacy relabeling.

Same pinned cached WSLc image217851fe68e7/linuxamd64/Python3.13.5/Tk8.6;
private Xvfb :97/Openbox/US keymap, source and auditor inputRO/networknone,
uid65534, own outputs. CPU0.5/512M are requests only; swap/cgroup enforcement
warnings, nonrootX11/Openbox/Fontconfig logs remain. No resource/OOM/WSLc-vs-
Docker performance claim, userdisplay/GPU/model/external effect, shared
restart/globalconfig or another owner's allocation change.

Prospective#5260#5970445861/#5085#5970446028; release#5085#5970456121.
RawSHA256 `8b3dd535fd6d7137bf58a71592fcfa5d3f7fc0fa0f45e6bd6485be49f997f7b3`;
auditstdout `3c6214e2e97573530be3fa31222087803b443b3ac593cc70777d21498a923d4c`.
Keep#5260/#5296 and the broader roadmap open. Prior A02 STOP, A03 no-input
and A04 method evidence remain immutable. No production/default timing fix.
