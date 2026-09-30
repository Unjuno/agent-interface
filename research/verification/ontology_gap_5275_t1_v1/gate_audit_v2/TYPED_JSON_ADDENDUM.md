# Typed-JSON comparison addendum

The frozen `retained-01/CONTROLS.json` record named `integer_gate` contains
`changed_from_original: false`. This diagnostic used Python dictionary
equality, which equates integer `1` with Boolean `True`; it cannot distinguish
their JSON types. The retained mutation payload correctly contains integer
`1` at `gates.all_cases_accounted`, while the original raw contains Boolean
`true`. Their canonical JSON encodings differ.

The substantive audit outcome is unchanged: the original auditor accepts
this copy, and the successor independently rejects it with error `gates`
using strict Boolean typing. The frozen diagnostic, raw control payload,
source and first result are preserved rather than edited or rerun.

This addendum corrects interpretation of that one diagnostic field only.
It is not a new verification allocation or scientific result.
