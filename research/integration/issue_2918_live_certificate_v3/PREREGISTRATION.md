# Issue #2918 live certificate transfer — allocation 03

## H/T/D/C/U

**H — hypothesis.** The #1904 minimum state-conditioned certificate can be
derived from fresh pixels returned by the public X11 observation API, and
reuse of the previous certificate may suppress forwarding for changes outside
that previous certificate's dependency mask. Masked changes and all uncertain,
stale or unbound observations must fail open. Allocation 01 STOP and allocation
02 HOLD remain immutable and are not rerun.

**T — one bounded formal allocation.** Repeat the same frozen 12-case schedule
as a new allocation, without changing hypotheses, thresholds, masks, or
expected dispositions. Allocation 02 showed the intended two unmasked
SUPPRESSes, masked FORWARD, and seven YIELDs, but did not retain complete
lineage for two fail-open cases and its audit report was not saved. Allocation
03 uses an additive runner that records observation ID, raw and PNG hashes,
actual XID, target binding, intent epoch, capture interval, decision time and
prior certificate context for every case. The independent auditor requires
those fields, reopens all 11 PNGs, independently derives terminal decisions
and writes its report to a separate writable mount while raw inputs remain
read-only. Ambiguous-target case remains a zero-observation YIELD.

**D — decision.** `PASS_LIVE_MANIPULATE_CERTIFICATE_SCOPED` only if the frozen
auditor exits zero after verifying all 12 case rows; all 11 public API return
receipts and their matching exact XIDs/bindings/epochs/times/hashes; the
ambiguous case has exactly two role matches and zero API calls; both safe
unmasked transitions suppress using the prior mask while phase-union/global
controls forward; the masked transition forwards and changes the independent
terminal decision; all seven uncertainty controls YIELD; no input is emitted;
and all raw checksums reconcile. Any missing field, assertion, output write,
or container/setup failure is recorded as HOLD/FAIL/STOP, not PASS. Run one
formal container invocation and one read-only-input auditor invocation. No
retry or source edits after the formal start.

**C — constraints.** OrbStack Docker 29.4, local immutable linux/arm64 image,
`--network none`, read-only source/root and raw audit mount, private Xvfb,
explicit `/repo` Python import root, fresh allocation-specific runner output,
and separate audit report mount. No model/provider, external network, GUI
input, real-app data, production claim, or action/effect claim. Reuse the exact
candidate/compiler from allocation 01 without modification.

**U — unknown.** Whether live pixel evidence and caller-visible binding/epoch
lineage make exact state-conditioned dependency narrowing safe and useful at
this observation boundary. The private deterministic fixture cannot establish
real-application effects, end-to-end observation cost savings, or product
readiness.

## Frozen source and commands

Allocation 02's actual 12-case HOLD evidence is at
`research/integration/issue_2918_live_certificate_v2/`. Allocation 03 runner,
auditor, import root, image ID and exact commands are frozen in
`SOURCE_FREEZE.json`. Construction checks are compile/import plus a negative
audit control against allocation 02's known incomplete lineage; those checks
do not call the observation API or alter either predecessor allocation.
