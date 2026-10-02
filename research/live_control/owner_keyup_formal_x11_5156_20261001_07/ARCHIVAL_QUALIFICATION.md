# Allocation 07 archival qualification

The 19 original files in this directory are copied unchanged from source tip
`6a6bf675f9f17711b907f7d8e61d575b97c9581b` on
`research/5156-owner-keyup-x11-a07-20261001`. This archive adds only this
qualification and `README.md`.

The source `STOP.json` records `STOP_RESOURCE_COORDINATION_BEFORE_CANDIDATE`:
four nonterminal `Created` containers had unresolved ownership/release status.
The required response was to avoid inspecting, stopping, removing, or otherwise
altering them. Candidate=0, independent auditor=0, container starts=0, image
inspections=0, and scientific result `NOT_EVALUATED`. This is not a negative or
positive result for the KeyRelease/XSync hypothesis.

Any local test validation is limited to pure construction/audit fixtures; it
does not execute the frozen runner, auditor on formal raw, Docker, Xvfb, GUI, or
input. Local CPython 3.14.5 validation passed 23/23 tests, including only
synthetic audit fixtures and launch-contract construction. This archive does
not renew the consumed allocation, authorize another container slot, or change
any predecessor/successor evidence.
