# Local System-1 research

This directory contains low-latency local decision/kernel experiments: route-decision cost, bounded receipt use, typed evidence gates, time-to-collision admission, and useful work during frontier gaps.

It is narrower than [`../system1/`](../system1/): this namespace focuses on local execution/decision mechanics and cost, while `system1/` retains related representation/exit/last-effect experiments.

The current project invariant still preserves rich-model intent; local decision mechanisms operate only inside bounded authority with fresh evidence.

## Track map

| Theme | Retained studies |
|---|---|
| Compiled/local decision kernel | [`compiled_typed_decision_kernel_v1/`](compiled_typed_decision_kernel_v1/), [`cross_domain_rule_vm_v1/`](cross_domain_rule_vm_v1/), [`cross_domain_rule_vm_v2/`](cross_domain_rule_vm_v2/) |
| Route-decision cost | [`route_decision_cost_v1/`](route_decision_cost_v1/), [`route_decision_cost_v2/`](route_decision_cost_v2/), [`route_decision_cost_v3/`](route_decision_cost_v3/) |
| Time-to-collision / stable admission | [`direct_ttc_v1/`](direct_ttc_v1/), [`direct_ttc_v2/`](direct_ttc_v2/), [`stable_ttc_admission_v1/`](stable_ttc_admission_v1/), [`ttc_consecutive_confirm_v1/`](ttc_consecutive_confirm_v1/) |
| Typed evidence gating | [`typed_evidence_gate_v1/`](typed_evidence_gate_v1/) |
| Receipt use / transfer | [`bound_receipt_use_cost_v1/`](bound_receipt_use_cost_v1/), [`map01_last_effect_receipt_transfer_v1/`](map01_last_effect_receipt_transfer_v1/) |
| Useful work during frontier gaps | [`useful_work_per_frontier_boundary_v1/`](useful_work_per_frontier_boundary_v1/), [`useful_work_per_frontier_boundary_v2/`](useful_work_per_frontier_boundary_v2/) |

## Interpretation

- These studies measure or constrain bounded local mechanics; they do not authorize arbitrary semantic decisions.
- A faster local decision path is useful only if freshness, authority, and task-effect correctness remain intact.
- Deterministic rules/servos remain preferable when sufficient; a learned local supervisor is justified only by a demonstrated residual.
- Component-level results do not establish integrated human-tempo control.

## Read next

- Related representation/exit studies: [`../system1/`](../system1/)
- Current objective: [`../../docs/CURRENT_GOAL.md`](../../docs/CURRENT_GOAL.md)
- Research method: [`../../docs/RESEARCH_METHOD.md`](../../docs/RESEARCH_METHOD.md)
- Evidence ledger: [`../../RESEARCH.md`](../../RESEARCH.md)
- Workspace map: [`../README.md`](../README.md)
