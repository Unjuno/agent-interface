# Undo admission under an unchanged visible projection

SUPPORT_ANALYTICAL_BOUND_SCOPED. This is an analytical consequence of the two
actual R02 worlds in merged #7309, not a new LibreOffice/model experiment or
additional success sample. Separate offline certificate/audit each exit0;
the audit reconstructs the full declared before-Undo projection and joins both
original after-Undo rows to saved read-only reopen cells and file hashes.

Declared policy input is ONLY current A1/B1 strings, visible Undo titles,
undo availability and lock flag. It excludes scorer-world labels, recording
history, document IDs and file hashes. Both observed worlds project to exactly
the same canonical bytes, SHA256
63bae76d0fd08c4e89c9f0ba54ccdf764ee2c51814157bede9f7fb14243ae3af.
Actual Undo leaves A1 empty in both, but preserves B1=PROTECTED in single_visible
and empties B1 in hidden_attached. Recording histories differ intentionally.

Proof: for any deterministic or randomized policy whose only input is this
projection, let p be its probability of choosing Undo. Its input is the same
in both worlds, hence its p is the same. In the hidden-attached world Undo
loses protected B1, so loss probability there is p. If the declared gate
requires zero protected loss for EACH compatible world, p must be zero.
Declining Undo preserves B1 but supplies no demonstrated restoration of A1.
This is an exact restricted decision bound, not a frequentist estimate, equal-
prior Bayes error, reliability rate or an impossibility for every action.

Repeated unchanged-projection rechecks or extra model reasoning do not change
this input distinction. New observations that acquire informative recording
history, authenticated compensation footprint or causal ownership are outside
the bound and may change the decision. A model-facing trial should test access
to such information and actual preservation, not expect richer inference alone
to identify hidden history. No claim that actual model responses coincide or
that an actual repeated query returns an identical projection was measured.

Refinement of #7309's simple-reference guidance: a current-state recheck is
not sufficient merely because it is fresh; it must expose relevant new
provenance or find a changed state. SAVE_AS_NEW, targeted current-bound edits,
different views and explicit human/owner decisions are outside UNDO/DECLINE
and have no measured outcome here. ABORT avoids this Undo risk, but does not
establish successful compensation. No new selective-undo subsystem follows.

Source raw/reopen bytes copied literally from fixed public head63797a4ed;
source/main delivery628ce6ce86ba955c5665bcc6d76d819d5161d9ea. Old R01 HOLD,
R02 original XML audit FAIL and supplemental saved read-only audit remain
unchanged. B1 protection is authored, not independent external writer identity.
No original producer/auditor/Undo/model/native replay, no GPU/backend/app task
or cost measurement. WSLc offline readonly source mount/networknone/nonroot,
CPU1/memory512M requested, effective cgroups unsampled; swap warnings retained.
The full #2122 model/held-out/conflict/ownership task and #57/#59 remain open.
