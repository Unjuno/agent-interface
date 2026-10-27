# Evidence custody and scope

Transferred unchanged from PR #8627 head `f1b28260fbb35ea9b07f816783eaca32a9d28e58`. Both archive SHA-256 digests match the PR record; 39 capsule data-manifest entries match the bytes and lengths inside the archive. This is an integrity check, not an independent reproduction of the oracle. Neither the candidate nor auditor was rerun.

The reported result concerns a finite synthetic model with exact predicate and completeness generations assumed. It does not establish that a real GUI exposes complete atomic observations, or prove live task correctness, action safety, or performance. The original separate audit code was written by the same author; human nonauthor review is not claimed. See Issue #8613 and PR #8627.

An independent saved-row reconstruction is available in `verify_8613_saved_rows.py`. Run it with the retained `RESULT_CAPSULE.tar.xz` path; it reads only the raw member and does not run archived code. Normal and optimized Python both reproduced 77,700 rows, 1,277 safe histories, 13,465 NODE_ONLY unsafe and 1,266 ALWAYS_REQUERY unsafe admissions, with no certificate/oracle mismatch. One altered-row control was rejected by the pinned raw digest; four unsafe history controls and one safe control were checked. This is the same finite serial model, not an independent real-GUI or observer-completeness validation.
