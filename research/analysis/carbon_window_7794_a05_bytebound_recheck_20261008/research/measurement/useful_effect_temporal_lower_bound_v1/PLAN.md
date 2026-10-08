# Useful-effect temporal lower bound v1 — construction

H: Holding merged #941 occupancy/release/authority arithmetic fixed, an independently scored effect may count as bound only when its timestamp is nonnegative and not earlier than the referenced actuation down edge. Post-release effects remain eligible because application-effect latency has no proven upper bound.

T: Pure standard-library/container construction. First reproduce merged-v1 acceptance of pre-actuation and negative-timestamp effects. Then apply only a temporal effect-classification adapter. Fixed controls plus 100,000 seeded event cases and 50,000 fresh mixed multi-actuation traces. No #946 corpus/seed, no #869 live/formal allocation, no retained MAP01 reinterpretation.

D: Construction passes only if all negative/pre-actuation events are excluded from bound categories, exactly-at-down/later bound roles remain unchanged, unbound/unscored roles remain distinct, and every occupancy output is unchanged for identical wait/actuation inputs.

C: Strong external causal lineage could make this check redundant; delayed application effects can occur after release; live clocks may differ across processes.

U: Synthetic same-clock evidence only. No X11/MAP01/human-tempo/production claim. Formal authorization is false.