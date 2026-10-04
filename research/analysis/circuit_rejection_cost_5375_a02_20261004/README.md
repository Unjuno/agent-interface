# #5375 rejection-cost boundary A02

Fresh allocation `CIRCUIT-REJECTION-COST-5375-A02-20261004-01`. A01 remains immutable: its over-capacity candidate row and read-only-auditor STOP are not retried. This revised assay addresses those specific failures with one-tick bounded stage accounting and distinct candidate/audit output mounts.

## H / T / D / C / U

**H.** Under fixed demand and shared capacity, charging backend ingress/parse plus per-request reject/quarantine cost can starve a mandatory safety check under backend-only fail-fast, while upstream admission or a reserved safety lane preserves that check without losing eligible obligations.

**T.** Three eligible fixed one-tick strata: rejection-cost storm (8 offered, per-refusal cost 3), zero-rejection-cost control (8 offered, cost 0), and bounded normal load (2 offered). Compare backend-only breaker, upstream limiter (admits at most 2), and reserved safety lane; common capacity 19. Include one separately marked synthetic obligation-drop fault-control row. The independent stdlib auditor reconstructs every row from the frozen spec and separately rejects four mutations. Construction tests run before formal allocation. If preflight passes, run candidate once, then auditor once, each in separate WSLc containers, pull never, network none, CPU=1. No retries.

**D.** `PASS_METHOD_SCOPED` only if exact raw reconstruction and all resource/obligation invariants pass; storm backend safety=0 and both upstream/reserved safety=1; zero-cost backend and bounded strata preserve safety; the planted drop is detected and excluded; authority admissions remain 0. Else preserve exact FAIL/HOLD/STOP.

**C.** A reserved lane may protect safety without upstream filtering; zero-cost null may show no benefit; deferred work may remain backlog rather than recovery. All execution and deferred-work costs are charged; dispatch count is not the endpoint.

**U.** Synthetic integer resource units and a one-tick fixture only. No empirical Agent Interface costs, production workload, live resilience, task effect, latency or product claim.

## Frozen provenance

Current main at freeze: `13bab54ea6d91978247ecc1b70e5060db752367a`. Issue #5375 refinement: comment 5973345660; A01 prereg/result: comments 5975802101 / 5975814276; retained A01 package/STOP: Draft PR #7391. WSLc 3.0.1.0; cached image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`), Python 3.12.14, pull never, network none, CPU 1. Requested memory limits, if any, do not imply enforcement. Fresh source/output directories are used.
