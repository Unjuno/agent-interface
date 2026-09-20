# Issue #2918 live certificate transfer — allocation 02

## H/T/D/C/U

**H — hypothesis.** A #1904 minimum state-conditioned certificate, when its
facts come only from fresh PNGs returned by the public X11 `observe` API, can
safely suppress forwarding on changes outside the *previous certificate's*
dependency mask. A change inside the mask and stale, partial, missing,
contradictory, replaced, ambiguous or intent-mismatched evidence must fail
open. Allocation 01 remains an immutable setup STOP and is not repeated.

**T — one bounded formal allocation.** Reuse byte-frozen candidate/compiler,
fixture runner and independent auditor from allocation 01. Execute the fixed
12-case schedule from Issue #2918: complete initial/unmasked/masked transitions;
PREPARE abort initial/unmasked transitions; then missing, partial,
contradictory, >250ms stale, changed XID, ambiguous matching windows, and intent
epoch mismatch. Two first transitions are distinct held-out logical workflows
(completion and abort); all evidence is from a private disposable X11 fixture,
not authored Boolean inputs. Candidate receives only public-API image bytes and
caller phase/epoch/binding. Oracle data is stored separately, never read by the
candidate. One read-only independent auditor reconstructs pixels and terminal
decisions. No action is dispatched.

**D — gates.** `PASS_LIVE_MANIPULATE_CERTIFICATE_SCOPED` only if all 12 cases
are retained; the two safe unmasked transitions suppress using the prior
certificate mask while both phase-union and global-support controls forward;
the masked change forwards and changes terminal disposition; all seven
uncertain/control cases YIELD; capture bytes, XID, binding, intent epoch and
generation time reconcile; the independent pixel/terminal audit passes; and
there are zero unsafe suppressions. Otherwise preserve typed FAIL/HOLD/STOP.
No retry, threshold tuning, or source edits after formal start.

**C — constraints.** OrbStack Docker, immutable local linux/arm64 image ID,
network disabled, root/source read-only, private Xvfb, explicit
`PYTHONPATH=/repo`, separate fresh output volume. Only public read-only X11
observation; no model, provider, external network, real app data, GUI input,
task mutation, or production claim. This is allocation 02, a distinct
successor to the retained allocation 01 STOP; its output path is separate.

**U — unknown.** Whether live pixel-derived and epoch-bound facts provide a
safe useful narrowing at the public observation boundary, and whether
uncertainty is detected by the caller before a certificate is reused. The
private fixture does not establish real-application effect, observation-cost
savings, or production readiness.

## Frozen source and invocation

Allocation 01 is preserved unchanged at
`research/integration/issue_2918_live_certificate_v1/`. This allocation uses
candidate/compiler SHA-256 `8cd92785f15a388c07b44f3f98001950d1fd616d42c191395963fa0a75599ef5`,
runner SHA-256 `e67cda1ea204cfb7d29751de71d9690c619a953f47a5ab9bb86529cd78209d24`,
and auditor SHA-256 `a8a80e224872e5f6240a4a7945727de9fd564e0a8a8f365165fa7f6ea58881b0`.
The exact image, command, fresh output boundary and base commit are recorded in
`SOURCE_FREEZE.json`. The only setup correction from allocation 01 is the
explicit import-root environment setting `PYTHONPATH=/repo`; no candidate,
case, mask, threshold, expected disposition or auditor change is allowed.
