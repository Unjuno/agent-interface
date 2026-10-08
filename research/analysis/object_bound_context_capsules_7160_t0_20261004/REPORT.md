# Issue #7160 T0 result: PASS_METHOD_SCOPED

The candidate and independent auditor each ran once and exited 0. The auditor
reconstructed all 18 policy/case rows with no errors. IDENTITY_BOUND retrieved
the two same-object/same-generation cases (appearance change and moved object)
and returned zero wrong, recycled, duplicate-label, or unknown-identity cases.
Appearance and location are marked stale for revalidation. No row grants input
authority. All four planted corruptions were rejected.

The similarity-only baseline retrieves by repeated label, including wrong and
recycled objects; NO_MEMORY retrieves none. This establishes a finite
identity-contract distinction only.

## Limits

The fixture stipulates object IDs and generations. It does not measure visual
re-identification accuracy, hidden app state, semantic task correctness,
reduced model boundaries, latency, user benefit, or GUI safety. Capsules remain
context only and do not identify a live target or authorize input.
Host-only standard-library Python; no container-specific semantics were tested.
