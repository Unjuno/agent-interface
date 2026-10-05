# Reaudit A02 amendment

The first secondary auditor result in `results/reaudit-a01/AUDIT.json` is preserved as FAIL. It assumed an explicit nested route authority object that the candidate did not emit, repeating the shape mismatch found in original A02.

This version replaces that check with four explicit `input_release_transition` row checks for `grants_input_authority=false` and `physical_verification_authoritative=false`. All other source/input checks are unchanged. Candidate invocations remain zero; this is one versioned raw-only auditor invocation against the same immutable preserved candidate output. Output goes to a new `results/reaudit-a02/` directory. The original A02 audit and secondary A01 FAIL remain unchanged.
