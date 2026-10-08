# Retained multi-app transition integration audit — R0

Task: `MULTI-APP-TRANSITION-RETAINED-INTEGRATION-AUDIT-R0-20260918-001`

## H
Retained evidence covers focus drift, modal transitions, geometry drift, and window/process replacement, but not all four inside one frozen longer mixed-app session under one controller/correctness contract.

## T
Freeze exact source blobs for PHASED_FOCUS, SHARED_PHASED_CALC, GUARDED_HIERARCHICAL_DEOPT_REPORT, RESEARCH and ROADMAP. Normalize source-scoped transition flags. Formal computes coverage union and same-session four-way intersection only. Bounded search absence is not treated as proof.

## D
PASS iff all four transition families are represented somewhere, >=2 desktop apps are represented, integrated all-four rows=0, RESEARCH still records longer mixed-app sessions as future work, source identities are exact, and formal1/reruns0/replacements0/tuning0 with independent audit.

## C
Chromium GHD already combines geometry drift + real window replacement in one session; Calc modal handling includes focus transitions but is not arbitrary external focus drift. Those distinctions are preserved.

## U
Retained-evidence audit only; no claim about private/unpushed evidence, no new GUI/model/task input, no integrated performance claim.
