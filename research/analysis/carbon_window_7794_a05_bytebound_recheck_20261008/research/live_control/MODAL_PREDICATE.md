# Modal predicates must include action-relevant state

To investigate the 24–39 second Calc modal decision gap, probe_modal_focus.py
collects four actual UI states: default Excel button focus, then Tab to checkbox,
ODF button, and Excel button. Images were visually inspected. All four share the
same X11 focus ID and window list. This is fixture collection using the legacy
setup driver, not shared-runtime performance or a new controller.

Compared with the default screenshot, normalized whole-frame RGB mean absolute
error is 0.000428 for checkbox focus and 0.000927 for ODF focus. Within the whole
modal it is 0.004414 and 0.009566. A 0.03 whole-modal similarity threshold accepts
both despite changed keyboard target. The changed Excel-button region has error
0.035578 and 0.118755 respectively. X11 focus/title and broad appearance alone
are insufficient to establish the intended Return target. The probe does not
press Return on the negative states, so it does not assert their saved-file effects.

ModalVisualPredicate compares both modal and action region against a copied
template. At 0.03 for each, it abstains on both focus negatives and on initial/saved
sheet views, accepts default/restored Excel focus and three earlier recorded format
modals, and rejects unsupported image dimensions. Nine image cases are retained in
modal-predicate-01; source hashes/config are frozen. No images were synthetically
edited. The template, boxes and labels are development-known and were chosen after
inspecting this family, so this is not held-out evidence or threshold generalization.

Output is visual_candidate/abstain/unsupported_frame with authority=none and
semantic_verified=false. It neither executes input nor admits a speculative future.
Fixed pixel coordinates, locale, theme, image replacement, overlapping windows,
changed dialog wording and stale sequence/focus are outside its guarantees.
The focused-button test is necessary evidence for this action, not sufficient
semantic verification. A visually copied dialog can still match.

This counterexample defines the next experiment: a prepared Return branch must
bind action-relevant state and fresh window/frame/observation dependencies, then
pass ordinary admission. Alternatively, an explicit pointer target changes the
focus dependency but requires fresh target identity and coordinates. Do not choose
a branch from a weak modal match alone. Test concrete fresh variants and unexpected
states before using either route to remove the external decision boundary.
