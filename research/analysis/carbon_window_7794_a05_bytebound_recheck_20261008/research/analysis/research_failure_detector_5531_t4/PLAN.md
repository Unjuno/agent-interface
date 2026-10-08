# T4 — hierarchical common-cause boundary

Issue: [#5531, Separate liveness suspicion from verifier failure](https://github.com/Unjuno/agent-interface/issues/5531).

## H/T/D/C/U

- **H:** Under a declared site-level failure model, counting distinct observer or rack names can overstate independence. Grouping current crash witnesses by their configured site prevents a shared-site witness set from producing a terminal `FAILED` classification, while two independent site witnesses can still cross the toy threshold.
- **T:** Run five deterministic cases with generation 7, site path `[site, rack, host]`, a site-level cut at depth 1, and a two-site threshold. Include same-rack/different-host, different-rack/same-site, distinct-site, stale-generation, and one-observer/two-site-placement cases. A separately written raw-output auditor uses literal expected classifications and does not import candidate logic.
- **D:** PASS only if candidate and independent auditor agree on all five predeclared states and counts, the auditor rejects a mutation that promotes same-site evidence to `FAILED`, and both isolated Docker processes exit 0. Any other result is retained as FAIL/STOP; no retry of the frozen candidate allocation.
- **C:** Existing typed suspicion/independent-witness rules may already be adequate when fault domains are correctly declared; this aggregation can add false suspicion or implementation complexity without real benefit.
- **U:** Site labels and their failure meaning are supplied by the fixture, not discovered or empirically validated. Shared global control-plane, network, cloud, and correlated-site failures are outside this finite model. No real timing, failure probability, production availability, authority, or GUI claim follows.

## Boundary semantics

The first `domain_path` component is the configured site-level independent failure domain; rack and host are nested identifiers and do not add independent witnesses at this cut. The common global infrastructure above sites is deliberately outside the declared model. A repeated observer claiming multiple sites is ambiguous and excluded rather than counted in both.

## Allocation policy

Construction tests are local and non-allocating. The formal candidate is run once in a network-disabled, read-only Docker container pinned by local image ID. A second fresh container receives only `audit.py` and the candidate JSON. Preserve exact stdout and exit/inspection metadata. No setup or failed formal run is retried.
