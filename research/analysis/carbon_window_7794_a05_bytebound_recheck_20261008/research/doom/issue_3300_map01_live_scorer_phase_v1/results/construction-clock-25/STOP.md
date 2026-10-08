FAIL_CONSTRUCTION_INTEGRITY — mismatched WAD and missing image identity

Three clock-driven construction rows were produced, but this invocation is
invalid for Issue #3453: it used the ViZDoom 1.2.3 package-bundled WAD
(SHA-256 `729f100448d0b48e12ecc8004e096a9ea6df024467d962f002bb286805be3a8e`)
instead of the frozen Freedoom 0.13.0 WAD
(`a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`), and
the runner was not given `--image-id`. Independent audit therefore reports
`FAIL_CONSTRUCTION_INTEGRITY` with three provenance errors. Do not pool or cite
these rows as valid construction measurements. Raw, audit, and logs remain
unchanged. The corrected, separately allocated run is construction-clock-26.
