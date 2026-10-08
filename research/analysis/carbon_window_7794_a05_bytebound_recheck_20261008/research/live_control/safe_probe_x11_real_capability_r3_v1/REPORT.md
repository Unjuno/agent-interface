# Safe-probe X11 real-capability R3 — retained result

Issue #1910. Parents #1716/#25/#40. Direct predecessor #1899.

## Disposition

**PASS_SAFE_PROBE_X11_REAL_CAPABILITY_R3_SCOPED**

Formal1 / reruns0 / replacements0 / tuning0.

## One changed factor

R2 used a synthetic fixture-owned `_AI_CAP_MODE` property. R3 replaces only that capability source with actual X11 extension availability from read-only `QueryExtension("XTEST")`.

Two private Xvfb servers are kept alive:
- default server: XTEST present;
- `-extension XTEST` server: XTEST absent.

Each server hosts two Tk windows A/B; fixture setup changes only focus A/B to author independent states.

## Safe probes

- FOCUS_QUERY: GetInputFocus, declared request/reply cost1, partition [2,2].
- CAP_QUERY: QueryExtension("XTEST"), cost1, partition [2,2].
- FULL_QUERY: focus + extension + geometry, cost3, partition [1,1,1,1].
- GEOMETRY_QUERY: geometry only, cost1, partition [4].

The unsafe perfect discriminator remains metadata-only and has no executable implementation. No XTEST injection API is imported or invoked.

## Formal

256 logical cases,64 per hidden state:

- exact identification: optimal256/256, greedy256/256;
- optimal #1874 tree: two safe probes / cost2 on256/256;
- one-step residual-greedy: FULL_QUERY / cost3 on256/256;
- unsafe executions0;
- XTEST action calls0;
- candidate state mutations0;
- before/middle/after/final focus+capability stable256/256;
- live partitions exactly FOCUS[2,2], CAP[2,2], FULL[1,1,1,1], GEOMETRY[4].

Primary audit passes five corruption controls. Independent audit checks raw QueryExtension/focus receipts for256 rows and imports no candidate implementation; errors[].

## Interpretation

The safe-probe decision-tree ladder now transfers from analytical partitions (#1836/#1874), through a synthetic X11 capability bit (#1899), to a real backend capability bit.

The result is deliberately narrow: QueryExtension says the X server exposes XTEST. It does **not** say the current session is authorized to use XTEST, and the candidate never uses it.

This strengthens the distinction:
`capability discovery != authority`.

## Integrity

- source bundle Git blob: `a208bf1df5d8f48e3e50cf81702348c041edd51f`;
- formal raw SHA-256: `000bd28ee13702dc63013577e868b65f6a3ad5af9756f37490694c2e7932c9f7`;
- primary audit SHA-256: `f04a5e025c7b6b1aa8bc813316ef76b5733e2ab892e55bf727ac04acc3a80fd4`;
- independent audit SHA-256: `a03dc78954c30be4604a18de36f66bdf0d504e8fad043e34a2e7d5ee3debd3ac`.

The full812,862-byte formal row result is hash-identified but not embedded. Main retains exact source, aggregate formal result, both audits and the publication boundary.

## Scope / next rung

Private-X11 only. No capability-negotiation planner benefit, task input, model/token/latency/human-tempo/general-GUI claim.

The next useful capability study is not another synthetic bit. It should test whether a session-scoped capability snapshot can combine real backend capability discovery with freshness/scope/authority separation and typed fallback without over-advertising execution permission.
