# Issue #4276 — near-tie ambiguity via calibrated score intervals

## H
If each region's latent score is guaranteed to lie in [s-e,s+e], select every region whose upper endpoint is at least the maximum lower endpoint. This possible-max set must retain every feasible latent maximizer and exclude certainly dominated regions. Point TOP1 is the negative comparator.

## T
64 frozen rows, four regions each: CLEAR_SINGLETON=16, NEAR_TIE_POINT_WRONG=24, OVERLAP_MULTI=12, EXACT_TIE_COMPATIBILITY=12. Integer score units only. One formal invocation after source freeze. Independent auditor does not import candidate helper functions. No GUI/model/network/input.

## D
PASS_INTERVAL_AMBIGUITY_SET_SCOPED iff 64/64 valid; possible-max reconstruction 64/64; latent true-max retained64/64; dominated inclusions0; clear singleton16/16; exact-tie compatibility12/12; TOP1 misses all prospectively directed near-tie truth rows while candidate misses0; authority grants0; raw audit errors=[]; >=10 corruption controls reject; formal1/reruns0/replacements0/tuning0.

## C
Intervals are authored/calibrated inputs; no claim about how a real detector obtains them. Candidate-set inspection cost belongs to #2751.

## U
No natural score distribution, real GUI detector/model benefit, tokens/latency, action authority or production claim.
