# Live pre-input guard over the shared executor

guarded_modal_backend_v2 is an experimental Backend subclass with a private,
one-shot arm_modal(program_id, proposal) attachment. A matching first Return step
samples current X11 binding and pixels, revalidates the bound proposal, then calls
the existing key path. The ordinary executor lease/sequence and owner checks still
apply. Guard failure produces needs_decision before that key executes. Diagnostic
publication/image saving occurs after the decision/execution path, avoiding a new
diagnostic I/O stall between checking pixels and dispatching the ordinary step.

The live fixture driver prepares Calc values and opens the format modal. Only the
guarded confirmation goes through this shared Backend/Executor; setup is not part
of its performance measurement. Independent scoring is after controller closure.

| Cohort 02 case | Guard result | Program | Saved required cells |
|---|---|---|---|
| Unchanged state | requires_new_admission | completed | 532, 590 |
| Tab changes internal focus to ODF | pixels_changed | needs_decision | empty |
| Move dialog | geometry_changed | needs_decision | empty |
| Wait beyond 250 ms proposal age | expired | needs_decision | empty |
| Proposal from another named session | session_changed | needs_decision | empty |

All release checks pass. Negative cases keep the same input-owner revision across
the guarded step, with no owned keys/buttons. The audit checks saved workbook values,
eleven exact public observation frames across both cohorts, five v2 pre-input sample
images and listed source hashes. Guard samples are separate internal evidence;
they do not advance public observation sequence. Current Context capture_ns refers
to the original source capture; fresh sample time is recorded separately.

V1 cohort 01 has four cases and lacks archived fresh guard images. Review found
its current session field copied from the proposal, making that comparison tautological.
V2 reads self.session.name and includes a wrong-session negative plus fresh samples
and owner states. V1 evidence is retained without attributing session protection to it.
The session name is currently an X display name and can be reused after restart;
it is not a cryptographically unique runtime incarnation or authentication token.

This is scripted known-fixture integration, not actual-assistant self-use, a public
operation schema, or a measured reduction in planner boundaries. Arm attachment is
private/trusted and optional; unrelated program IDs still use normal execution.
No general branch arbitration or cross-domain maturity is established.

The visual check and key input are not atomic. Ordinary owner checks catch their
existing focus/lease invalidations but cannot detect every same-window internal
focus change after the pixel sample. Whole-frame equality may reject unrelated
animation. Copied dialogs, identity ambiguity and scale changes remain unresolved.
Next bind a trusted runtime-incarnation ID and test changes between guard and input;
use these limits explicitly before allowing any prepared branch to replace a planner
decision. No speedup or safe universal Enter policy follows from this cohort.
