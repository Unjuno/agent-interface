# Research Preview readiness audit — 2026-09-19

This is an evidence-indexed gate record for Issue #58. It does not declare the preview ready.

## Current disposition

HOLD_RESEARCH_PREVIEW_NOT_READY

The repository has retained scoped component and integration evidence, but the release gate still lacks a verified one-command golden desktop demo, a runnable package/checksum/smoke test, and an honest continuously advancing DOOM showcase artifact.

## Gate matrix

| Gate | Status | Evidence / gap |
|---|---|---|
| Golden desktop workflow | HOLD | Issue #57 retained one fixed six-task allocation with independent scoring; a reproducible packaged demo is not verified here. |
| Reconstructable benchmark numbers | PASS_SCOPED | PR #2051 and retained #57 evidence preserve fixed-scope measurements; broad efficiency claims remain disallowed. |
| README separates proven vs research-stage | PASS_SCOPED | README states Research Preview and scope limits; this audit does not replace a release review. |
| Architecture explanation | PASS_SCOPED | README/docs architecture links exist on main. |
| DOOM showcase | HOLD | MAP01 R1 physical occupancy is scoped evidence only; no retained uninterrupted normal-speed MAP01 clear video is verified. |
| Runnable package/archive | HOLD | No checksummed downloadable runtime artifact was verified in this audit. |
| Supported OS/backend statement | HOLD | Evidence remains primarily Linux/private-X11 and scoped desktop fixtures. |
| Smoke/self-check | HOLD | No release-bound smoke command and artifact were verified. |
| Recovery/observation integration | HOLD | Roadmap still marks O3/O4, guarded policy, runtime consolidation, and stabilization incomplete. |

## H/T/D/C/U

H — A machine-readable readiness matrix can prevent a scoped research PASS from being misrepresented as a release-ready product.

T — Freeze the current main evidence links, evaluate each Issue #58 gate against retained artifacts, and run a schema validator that rejects missing status/evidence fields.

D — HOLD_RESEARCH_PREVIEW_NOT_READY unless every required release gate has resolving evidence. This record is valid when all rows are explicit and no unsupported claim is promoted.

C — This is an audit/index artifact; it does not run GUI, model, network, packaging, or DOOM work and does not alter historical results.

U — Actual user installability, checksum reproducibility, golden-demo execution, and video synchronization remain unverified.

## Next bounded successor

Create a fresh release-preparation successor for the golden desktop path. It must freeze the exact setup/runtime dependencies, execute the retained independent scorer in a disposable environment, retain first setup/runtime/semantic outcome, and add a checksum plus smoke command only after the demo is reproducible. A DOOM showcase remains a separate evidence lane.
