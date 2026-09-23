# Observation-bound modal proposals

bound_modal_proposal.py adds an immutable context and copied image digest to a
translated visual candidate. Context includes session identity, observation sequence,
capture time, window, focus and client geometry. Proposal expiry is capture time plus
a declared maximum age (default 250 ms); prediction/inspection time does not renew it.
Unequal before/after capture context, invalid age and size change yield no proposal.

Revalidation requires the same supplied context and pixels, rejects a clock before
capture or at/after expiry, and names the changed dependency. A pass returns
requires_new_admission, never an action, lease or ownership token. Hashing here only
detects changed bytes; it does not authenticate the caller or prove a real capture.

probe_bound_modal.py reuses the four frozen translated Calc images. Both Excel
states create proposals; both ODF states abstain. For each positive it tests changed
session, sequence, capture time, window, focus, geometry, alternate ODF pixels,
expiry boundary, clock rollback and unstable capture samples. These clocks and IDs
are synthetic. They are offline consistency checks, not live invalidation or
cross-thread admission evidence. Results and source/image hashes are frozen in
results/bound-modal-01.

Only trusted in-process code should construct these objects; direct construction
can bypass propose(). Passing a fabricated Context is not prevented. The module
does not read live X11 state, consume proposals, arbitrate branches or close the
race between validation and input. It cannot recognize copied dialogs or semantic
text changes that the visual predicate misses. Equal metadata samples are not atomic
state. Full-frame digest equality can also reject unrelated benign animation.

This makes required dependencies explicit before connecting prepared branches.
Next obtain context from the real observation/admission path, expire or discard
stale proposals, and verify ordinary owner checks immediately before any authorized
input. Do not give this proposal constructor an input method or infer authority
from a successful visual match. No planner-boundary savings are measured yet.
