# Preregistration — Issue #8150 T0

Allocation: `RUNTIME-ELIGIBILITY-8150-T0-20261005-01`  
Base main: `aeed696ff756d68497faed39b92e3546cb144972`  
Additive branch: `research/8150-threat-profiled-runtime-eligibility-t0-20261005`  
Package: `research/analysis/threat_profiled_runtime_eligibility_8150_t0_20261005/`

## H / T / D / C / U

**H.** A per-workload threat/asset/control card will identify at least one material mismatch in a runtime-name/default-route checklist, without increasing false eligibility, on this finite evidence set. It must distinguish observed, configured/requested, unsupported, and unknown controls; unknown is never satisfied.

**T.** Method-only review of the seven frozen workload profiles in `cases.json`, using only current-main policy blob `.github/wslc-local-containers.md` (blob `1e5146a91f19b947d1fca0dfb83eeccb04e01844`), the pinned issue/PR receipts below, and the cited official sources. No container, WSL, WSLc, Docker, network, process, memory-pressure, or filesystem probe will be run. Two reviewers independently classify required controls, evidence grade, and runtime eligibility without seeing the card's generated outcomes. The candidate card applies a frozen requirement×evidence rule; the baseline uses the policy's explicit runtime-selection checklist without adding a threat-profile card.

Evidence grades are:
- `OBSERVED`: retained non-adversarial receipt directly demonstrates the requested property for its scoped fixture.
- `CONFIGURED`: command/runtime configuration requests the property, but no independent behavioral observation establishes it.
- `DOCUMENTED`: authoritative documentation states a boundary/limitation or supported capability.
- `UNKNOWN`: no admissible evidence or insufficient attribution.
- `CONTRADICTED`: retained evidence directly conflicts with the requirement.

A profile may be called `ELIGIBLE_SCOPED` only when every mandatory control is supported at the profile's declared assurance level and the runtime boundary matches its attacker/trust assumptions. `HOLD` means a required fact is unknown/config-only below the required level. `INELIGIBLE` means documented or observed mismatch. These labels do not authorize a runtime launch.

Frozen profiles:
1. Trusted, standard-library, single-container CPU replay; a pinned image and read-only input are required; no adversarial code, host secrets, Compose, or hard memory ceiling.
2. Arbitrary untrusted code/artifacts; Windows-user files/credentials and peer workloads are protected assets; containment against malicious code is mandatory.
3. Trusted CPU job with a hard effective memory ceiling of 128 MiB required to protect a co-resident workload.
4. Trusted integration test whose frozen protocol requires Docker Compose/Engine API.
5. Trusted code, but outbound network denial must be independently demonstrated (configuration alone is below the declared assurance requirement).
6. Trusted replay requiring a read-only source bind that demonstrably rejects writes and a separate output path.
7. Any isolation-requiring workload for which the runtime identity/configuration/owner evidence is unknown.

Frozen mutations:
- M1: Remove the retained `EROFS` write-rejection observation for profile 6; a card must no longer call the read-only property observed or retain eligibility on that basis.
- M2: Relabel WSLc's accepted memory request as an effective cap while retaining the 384 MiB counterexample; the inconsistency must be flagged, never PASS.
- M3: Omit the Windows/WSL trust-boundary assumption from profile 2; the card must return HOLD/UNKNOWN, never inherit default WSLc eligibility.

Reviewers return per-profile mandatory controls, runtime/control evidence grades, and one of `ELIGIBLE_SCOPED`, `HOLD`, or `INELIGIBLE`, plus mutation findings. Agreement is measured with linearly weighted Cohen's kappa on the three ordinal outcomes; no ties are adjudicated by the candidate author. Threshold: κ ≥ 0.70, all planted mutations caught, unknown controls never satisfied, and no false eligibility for profile 2. H is falsified if no baseline/card mismatch is found, the card adds false eligibility, or reviewers cannot meet the frozen threshold. Otherwise any result is still method-only, not runtime certification.

**D.** `METHOD_PASS_SCOPED` only if the two independent blind classifications meet all frozen criteria above and the card beats the mechanical baseline on at least one material mismatch without false eligibility. Otherwise retain `FAIL_METHOD` or `HOLD_REVIEW_DISAGREEMENT`. No T1 or security-certification claim follows.

**C.** The existing policy already identifies several limitations (Compose/API, effective cgroup/swap, Docker availability). The card may only add review burden, and the small finite profiles may not expose a useful difference. Historical receipts are scoped and not current runtime readiness.

**U.** No exploit resistance, host/kernel isolation, hostile-code containment test, network-block enforcement, current WSLc ownership, effective runtime health, memory cap, Docker parity, real workload safety, or speed/memory benefit is established.

## Pinned evidence (read-only inputs)

- Current main and README/CURRENT_GOAL/ROADMAP intake: `aeed696ff756d68497faed39b92e3546cb144972`.
- Runtime-selection policy: `.github/wslc-local-containers.md`, blob `1e5146a91f19b947d1fca0dfb83eeccb04e01844`.
- #7924: `WSLC_CLIENT_OWNERSHIP_UNKNOWN + CURRENT_MAIN_CHECKOUT_MISSING`; no further WSLc management/RPC before explicit gate clearance. Its comments preserve #7970's no-further-operation gate.
- #6355: audit of a previous memory-cap failure; retained output records a 384 MiB allocation under requested 128/512 MiB settings.
- #6337 / PR #6352: one scoped WSLc portability run for a finite CPU fixture, not a security, Docker parity, or memory guarantee.
- #6561 / PR #6609: one prior synthetic method allocation in WSLc; not a current runtime-owner or security-boundary receipt.
- #6693: same-host Docker comparison is unrun and gated on runtime parity/ownership; excluded from cost claims.
- Public sources: Microsoft WSL security model (https://github.com/microsoft/WSL/blob/master/doc/docs/technical-documentation/security.md); NIST SP 800-190 (https://csrc.nist.gov/pubs/sp/800/190/final); current WSL Containers documentation (https://learn.microsoft.com/en-us/windows/wsl/wsl-container).

This preregistration freezes a documentation/receipt-based T0 only. It expressly does not clear #7924/#7970 and authorizes no WSLc operation.
