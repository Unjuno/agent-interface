# #1739 — retained XTerm resource-footprint transfer

## H
The #1730 RW/WW footprint predicate classifies the retained #1707 independent overlap as OVERLAP_ELIGIBLE and the shared-file overlap as SERIAL_CONFLICT. UNKNOWN fails closed.

## T
Pure offline standard-library classification over a declarative fixture derived from #1707's published arm semantics and pinned Git identities. No X11/XTEST/model/network/runtime action. Negative controls: omit shared_file, alias surfaces, UNKNOWN.

## D
PASS iff independent=OVERLAP_ELIGIBLE; shared=SERIAL_CONFLICT; UNKNOWN=SERIAL_UNKNOWN; omitted shared_file falsely admits the unsafe arm; surface alias serializes the independent arm; published outcome directions agree; exact source identities match; formal1/reruns0/replacements0/tuning0.

## C
Footprints are manually declared from known semantics, not discovered automatically. Hidden dependencies can invalidate the classification.

## U
Posthoc applicability only. #1707 remains unchanged and #1710 remains the owner of timestamp-audit repair.
