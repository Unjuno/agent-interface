# #1720 Phase-overlap resource-footprint serializability

## H
For deterministic two-intent phase programs with complete resource declarations, a pending first-intent tail may overlap the second intent only when the first tail has no read/write conflict with either second input or second tail. Under this sufficient condition, every admitted overlap schedule is observationally equivalent to whole-intent serial execution. Unknown declarations serialize. Surface identity alone is insufficient, and omitted dependencies can make an apparently safe overlap unsound.

## T
- Resources: r0,r1,r2.
- Two intents A/B, each with serialized input phase and pending tail phase.
- Phase operation vocabulary: READ, SET0, SET1, INC, COPYPLUS over the resources.
- Two initial states and both whole-intent serial orders.
- Exact declared footprints equal actual footprints for the primary theorem.
- If the first tail is conflict-free with both phases of the second intent, compare both legal overlap completion orders against whole-intent serial state and phase observations.
- Count a SURFACE_ONLY discriminator that overlaps every distinct-surface pair.
- Count an OMIT_ONE_DEP discriminator that removes actual conflicting resources from the first-tail declaration until the candidate admits.
- Directed UNKNOWN and reversed-conflict corruption controls.
- One formal invocation, reruns/replacements/tuning0; independent audit recomputes the space without importing candidate helpers.

## D
PASS_PHASE_OVERLAP_RESOURCE_FOOTPRINT_SERIALIZABILITY_SCOPED iff complete-footprint admitted overlap mismatch=0, conflicts serialize, UNKNOWN parallel admissions=0, SURFACE_ONLY mismatches>0, omitted-dependency mismatches>0, both intent orders are exercised, independent audit/corruption/source integrity pass, formal1/reruns0.

## C
The footprint may be incomplete or data-dependent; syntactic conflicts can still commute semantically; real event loops and hidden process/WM/filesystem state are outside this model.

## U
Analytical deterministic serializability contract only. No live XTerm/X11/model/token/wall-time/runtime promotion claim.
