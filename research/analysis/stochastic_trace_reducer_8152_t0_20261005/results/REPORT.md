# Issue #8152 T0 formal result

Base commit: `60aff39f60defd06f9b4cabd0941e54d17c570df`
Container image: `python@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151`

Disposition: `METHOD_PASS_SCOPED`
Audited method disposition: `METHOD_PASS_SCOPED`.

Raw audit valid: `True`; auditor errors: `0`.

## Method metrics

| Method | Search queries | Shorter instances | Held-out NI instances |
|---|---:|---:|---:|
| fixed_64 | 6912 | 12 | 12/12 |
| sequential | 4184 | 12 | 12/12 |
| single_run | 864 | 11 | 5/12 |

## Auditor disposition details

Sequential query advantage over fixed-64: `True`.

## Scope

Synthetic stationary hash-oracle experiment only. No live failure, GUI, model, or user data was used. A method-scoped PASS is not evidence of production reliability, causal root cause, general minimality, or deployment safety.
