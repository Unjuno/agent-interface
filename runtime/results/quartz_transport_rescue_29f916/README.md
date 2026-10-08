# Quartz original-review transport custody

Source29f916ae850139dae1f768be97a8226800c7bda8 contains three inert original
transport files. They bind original repair4dbc9898449eb9ba90bf9561c822700ecfd96641
and base9c26e204c0475bee30919e3d0e6681f393078ef1:194346patch bytes and29changed
postimages. Preserve them unchanged, without transferring historical approval.

The successor test reconstructs the exact full-index binary patch from Git and
checks all29postimages, prior blob identities/modes and original transport bytes.
It never imports the Quartz backend, creates native APIs, or emits input.

## Dependency and missing implementation boundary

Main still lacks this original tracked-release/error-receipt repair. However
original delivery #6938 now points toab14a6e0dc88353c4111196311a4dfbf5efd054a,
a newer draft with acquisition tracking and next-dispatch quarantine. Both its
remote ref and this transport ref contain4dbc9898. Replacing newer work with the
old29path patch, declaring old approvals applicable to the newer source, or
retiring this ref solely because a tag exists would be unjustified.

This batch preserves original transport custody only. It does NOT adopt the
missing Quartz implementation, claim native release safety, close #6938/parent
issues, or complete rescue of its production behavior. The next applicable
implementation integration must assess the newer acquisition/quarantine tests
and preserve original failures, receipt fields and actual next-dispatch bounds.
No physical release, ABI/TCC, concurrency, noncooperative native call deadline,
model/task or performance claim is made. Container image-store STOP remains;
no daemon reset/prune or shared input/resource manipulation was performed.

Source ref retirement remains pending fresh adoption, tag and head/base/descendant
dependency checks. Original patch whitespace must not be normalized to satisfy
lint; raw payload identity takes precedence for this inert witness.
