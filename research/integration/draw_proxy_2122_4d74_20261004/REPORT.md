# E02 target association mismatch — preserve first FAIL/HOLD

Base4751c849f0408e3157d5d7a8974815d60c06d07a. Eight NEW Draw documents, no model, one invocation/no retry; temporary/held/held/temporary/held/temporary/temporary/held proxy order. Same directed independent writer A1000→1700/B2000→2700 under undo recording lock; fresh current value comparison, setter1900,1000, immediate/100ms/1s reads, independent read-only UNO observer and saved FODG.

## Observed failure mechanism

Temporary proxy:2/4 tasks incomplete. Retained A proxy:4/4 complete. This small fixed sequence is not a natural rate, general retention guarantee, matched model benefit or production adoption gate.

Failed temporary cases0 and5 have **setter_name empty**, despite preceding source/admission snapshots naming A. Setter type is RectangleShape and logged argument1900,1000. Reading the setter proxy itself gives1900,1000; the fresh page view, separate observer process and saved FODG all retain real A1700,1000. B2700/shape dimensions500×500 are preserved. All six successful cases have setter_name A and all views agree1900. The immediate identity mismatch therefore joins the failed effect in these two new cases. Do not call setter-proxy position an independently verified document effect or infer that page index alone binds the validated target.

Original audit exits1/FAIL_OR_HOLD with `setter_or_observer` for the two failed cases: the failed conjunct is setter_name!='A', NOT observer transport; both observer exits0. Original data/source/gate unchanged. Producer/soffice parent0/errors[] does not make task PASS. No archived actor was replayed and older L01/E01 were not regraded. Their causes cannot be retroactively established because they did not retain this setter-name/proxy-view evidence.

## Primary-source interpretation

Inspected official tag25.2.3.2:

- https://github.com/LibreOffice/core/blob/libreoffice-25.2.3.2/svx/source/unodraw/unoshape.cxx (getPosition/setPosition near949–996; getName near1054–1065)
- https://github.com/LibreOffice/core/blob/libreoffice-25.2.3.2/svx/source/svdraw/svdobj.cxx (Move near1436–1454)
- https://github.com/LibreOffice/core/blob/libreoffice-25.2.3.2/svx/source/svdraw/svdotext.cxx (inspected, no runtime trace)

The shape setter/read methods distinguish an internal drawing object from cached position/name members. With an internal object, position mutation computes a displacement and invokes Move; without one, position storage can change without moving a document object. Name also distinguishes native object name from retained member name. This is source-level support for testing association/lifetime, NOT proof of the precise internal branch in our binary. The observed empty name/local1900/real1700 is consistent with lost object association; native pointer state was not instrumented. Public upstream tag is not independently bound to Debian's patched installed binary. No claim of a generic LibreOffice bug or a solved internal root cause.

## Integration implication

**SUPPORT_TARGET_BINDING_MISMATCH_SCOPED / HOLD_INTERNAL_CAUSE_AND_ADOPTION.** Current values checked on one lookup cannot authorize mutation through an unchecked subsequent lookup. A candidate should retain the SAME named shape reference, validate its identity/current state at the mutation boundary, refuse missing association, and independently verify actual effect. Name alone is not authenticated identity or ABA/current-document generation. Retention is a hypothesis-bearing construction control here, not sufficient proof of whole recovery safety. Stop arbitrary proxy/wait/model variants. No runtime repair or source adoption made.

Imagebab4dc0dff6ffa8270e86873c3987e0e3203c1b198a08ff971580a6c04c3ba1d/LO25.2.3.2. Source/plan/writer/observer/auditor/copiedE01 source frozen before execution. NoGUI/userdocument/provider/GPU; controlled writers are fixture-owned, not independently authenticated external ownership. No atomic revision/ABA/future-writer guarantee. Source bindreadonly/networknone/user65534, sampledCPU100000100000/memory536870912/pidsmax; swap warning retained. Parent terminal not complete descendant custody proof. Full2122/ROADMAP remainopen.
