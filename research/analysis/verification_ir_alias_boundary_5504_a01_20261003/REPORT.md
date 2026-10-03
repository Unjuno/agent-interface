# #5504 A01 — PASS_SCOPED_ANALYTICAL

The finite expressibility stop/control met its prospective gates. The result
supports the conditional criterion in PROOF.md, not current production IR
incompleteness, a CEGAR benefit, or an integrated runtime safety result.

One frozen host modelchecker and one independently authored read-only auditor
ran once each, both exit 0, COMPLETED, no timeout/interruption/retry. The raw
auditor reports PASS/errors empty: 32 rows, 16 restricted observable classes,
one conflicting class, 32 complete decisions. No formal allocation was rerun.

| Declared control | Retained result |
| --- | --- |
| Restricted four predicates | ONTOLOGY_INSUFFICIENT; 16 classes; one mixed class; no total correct table. |
| Conflicting witnesses | case_030 and case_031 share true,true,true,true visible evidence; required FAIL and PASS. |
| Complete five predicates | EXPRESSIBLE; 32 singleton classes, no conflict; 31 FAIL and one PASS. |

The all-visible-true mixed fiber proves that any total binary decision rule
using only the restricted projection must disagree with at least one required
label. The predeclared complete table is feasible. Case IDs are only witness
labels, never decision features. Repeated/renamed observations were construction
controls, not a learning trial. No primitive was inferred or authorized.

## H/T/D/C/U closeout

- H: modeled oracle realizable over projection iff constant on every fiber.
  Both directions are proved; this 32-state instance matches the criterion.
- T: exhaustive synthetic five-Boolean model, restricted4 vs complete5,
  with independent bit-mask reconstruction/raw-byte audit. Modelchecker can
  inspect the modeled oracle for feasibility; it is not oracle-blinded.
- D: PASS_SCOPED_ANALYTICAL because restricted stops with both witnesses,
  complete table is exact, formal audit is PASS, and streams/sources reconcile.
  ONTOLOGY_INSUFFICIENT is the expected negative control, not execution failure.
- C: labels and dimensions are designed assumptions; actual IR may already
  encode reversibility. This elaborates known alias prior art, not a new hidden
  predicate discovery or advantage over complete static ontology.
- U: actual concrete labels/projection legitimacy, production semantics,
  automatic extension authority, GUI/model/OS/timing, performance, memory relief
  and full roadmap remain NOT_EVALUATED. #5504 should stay open for actual IR.

## Frozen evidence identities

Recorded freeze UTC 2026-10-03T10:41:45.7635090Z precedes both formal attempts.
FREEZE.json SHA-256:
`c3540600aa8169dae41520c92fc11784c0a2fcacfcc2e576a437c4a0b038e907`.
Frozen source/schema/prediction hashes were checked before each launch.

- Modelchecker: 2026-10-03T10:42:38.207540Z start, PID 40928;
  raw stdout SHA-256 `82f34c5cfce51419b6044cb66fed06a32891b9b95c21cdc8d6015a6e0f33fba2`.
- Auditor: 2026-10-03T10:43:06.242357Z start, PID 22544;
  input digest equals the modelchecker stdout;
  raw stdout SHA-256 `2fa56596adff3adebfe00ca726a09b09696b0129bd073d335e7de1ff400089d0`.
- Both stderr files are empty (SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).
- Raw streams, initial attempt metadata and final receipts are in formal/.
  Sources remain the six reviewed Python files; receipts record identical hashes.

Windows Python 3.12.10 host execution is appropriate for this exactly determined
analytical question under the current RESEARCH_METHOD, whose anchored snapshot
is retained. Receipt wall-clock timestamps are provenance, not latency evidence.
Formal wrapper was direct/unfiltered capture v2, no runpy/source filter or
environment override. No process-level oracle isolation/durable hard-kill claim.

## Construction, review and custody

Retained combined construction suite: 112 passing fixture tests. Independently
authored auditor controls reject 92 actual changed-byte corruptions (75
structured/17 raw). These are test controls, not real-world rates. All first
REDs, capture repair, source-filter provenance limitation and two git whitespace
diagnostics are preserved in CONSTRUCTION.md and adjacent records. REVIEW.md
retains the initial Important finding and its verified repair, not only approval.
The cleanup exception Minor is bounded by initial evidence and the COMPLETED
gate; no universal interruption durability is asserted.

Original #5504 T0/T1/T2 and T0-01 STOP, PR #5544 negative benefit result, closed
#4294/PR4298, and #6645/#6997 evidence remain unchanged and unexecuted in A01.
Formal counts are host modelchecker/auditor/retry 1/1/0. Previously consumed
producers, WSLc/Docker container, GPU/model/GUI invocation counts are all zero.
No shared engine/VM/session/process/memory settings were changed. #5085 HOLD
is not lifted. The user's Docker-Desktop-free WSLc migration remains separate.

This directory is additive on an owned branch. SHA256SUMS.txt covers all retained
package files except itself. Integration uses hashes/fixture tests, not formal
regeneration; publication is a scoped main-based PR batch with exact subtree
readback. Publication/CI/main identities are recorded in the PR/Issue closeout,
not used to rewrite these scientific outcomes. Global roadmap is incomplete.
