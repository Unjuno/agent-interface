# Exact non-null power cross-check

The fixed audit design in `EXACT_POWER_AUDIT_DESIGN.md` exactly enumerates each arm's Binomial count distribution, maps each four-arm state to the six directed contrast decisions, and intersects those decisions across the three independent seeds. It evaluates the frozen +0.10 and +0.20 scenarios for both independent answers (60 Bernoulli trials per arm/seed) and perfect prefix clusters (6 trials per arm/seed). The threshold and the original simulation were not changed.

| Alternative | Dependence model | Exact gate rate | Monte Carlo rate | Difference (MC SE) |
|---|---|---:|---:|---:|
| +0.10 | independent answers | 0.3457371 | 0.346535 | -0.750 |
| +0.10 | perfect prefix clusters | 0.4972827 | 0.497745 | -0.414 |
| +0.20 | independent answers | 0.9285980 | 0.928525 | +0.127 |
| +0.20 | perfect prefix clusters | 0.6542304 | 0.656140 | -1.798 |

All four exact/Monte Carlo differences are within the predeclared five-MC-SE cross-check bound. The full machine-readable output is `NONNULL_POWER_EXACT_AUDIT.json`.

Reproduction command, run from this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 audit_nonnull_power_exact.py
```

The command exited 0. The audit source SHA-256 is `cb326c528c6d25748c98b6a1b24fdda32deb70a4f618e5c5ddebb08528560f12`; design SHA-256 is `6fc07363ce71a4ab8e80f6009cd73aeff7a225451305c5581b6803d2d937b3ca`; simulation input SHA-256 is `32e78a6b53388ca61ab7d878e5d1e7242e282eb7b269eb243ed23f29613c3b10`. Output SHA-256: `f2e5e80244bec2586ae24f0f75e5274de88d06a320f01b901356946a91e3dd57`.

This is a model-free mathematical cross-check conditional on the stipulated independent Binomial arm/seed draws. The cluster condition represents the frozen idealized perfect-prefix model. Neither condition measures Qwen3 behavior, GUI execution, or real within-prefix dependence; T1 remains `NOT_FROZEN_NOT_RUN`.
