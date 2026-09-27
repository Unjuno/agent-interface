# #1849 State-domain independence for multi-instance actuators

TASK: `MULTI_ACTUATOR_STATE_DOMAIN_INDEPENDENCE_R0_20260919_001`

## H
Distinct actuator instance IDs are not sufficient evidence of independent actuator resources. For already-authorized operations on otherwise disjoint surfaces, generic parallel admission is sound in the frozen abstract model iff their declared exclusive state-domain identities differ and no other exclusive resource is shared.

## T
Four same-modality actuator instances, three exclusive state domains, every 3^4=81 binding map, and all six distinct-instance pairs per binding =486 cases. Compare domain-aware candidate to independent resource-alias oracle. Device-ID-only comparator must expose all same-domain false parallels. Every alias case gets an explicit conflicting-write witness. Hidden-global-resource control tests declaration completeness.

## D
PASS iff candidate/oracle mismatch0, same-domain162, different-domain324, device-ID-only false-parallel162, alias witness missing0, hidden-global control discriminates, corruption controls pass, independent audit PASS, formal1/reruns0/replacements0/tuning0.

## C
Real backend state may include hidden queues, focus, grabs, compositor/application globals or ordering constraints. This theorem defines a capability contract, not backend compliance.

## U / stop
No live multi-seat, throughput, latency, GUI/driver, model or product claim. Stop after first deterministic formal result and audit.
