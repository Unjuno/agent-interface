# T0-v1 design review (addendum; original artifacts retained)

Post-run independent review found that `uncoupled_control` and
`coupled_near_boundary` in v1 used the same sequential dependency graph and
only changed the global deadline. The v1 scripts correctly computed their
frozen arithmetic, but that control does not instantiate the preregistered
uncoupled-vs-coupled structural contrast. Therefore v1's full T0 disposition is
**`T0_CONTROL_DESIGN_INCOMPLETE`**; its 32-schedule arithmetic and independent
replay remain valid within their narrow scope. Do not cite v1 as a complete
`METHOD_PASS_SCOPED`.

The original fixture, source, outputs, and hashes are not rewritten. A new
post-review v2 freeze is retained separately at
`../functional_coupling_5734_t0_v2/`. It addresses only the topology-control
defect with distinct parallel-vs-sequential DAGs. It is still synthetic and
does not establish the empirical Issue #5734 H, source-supported ranges,
baseline fairness, calibrated probabilities, or a live Agent Interface hazard.
