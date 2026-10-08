# Recovery status — Issue #4355

**Disposition: `HOLD_PREFORMAL_PACKAGE_FORMAL_RAW_UNAVAILABLE`.** The original remote branch package is preserved unchanged: its packed-index source/proof and 18-member preformal capsule. A network-disabled, read-only Linux/arm64 CPython 3.13.5 container ran the existing data-only `restore.py` into ephemeral `/tmp`; it restored 18 members / 152,251 expanded bytes with archive SHA-256 `a749c8b7adc628c3bcffb0c79c6cd0ae56beade648f2331225f9ac06d3090b11`. `packed.py` and `restore.py` parse, and the package JSON parses.

This is not a replay of the consumed scientific allocation. The branch contains the preformal capsule, not the formal raw rows/result/audit package. The Issue-reported scoped PASS/tradeoff therefore remains historical and is not independently re-audited here. The existing recovery notes report five of six construction checks passed; the remaining check stops before assertions because `construction/smoke02/01.raw.json` is absent. No fixture was invented and no formal run was repeated.

The published package supports preservation and bounded source review only; it does not establish the formal claim from repository-retained raw evidence or justify runtime adoption. Keep Issue #4355 open pending complete formal evidence recovery or an explicitly authorized, scientifically distinct successor.
