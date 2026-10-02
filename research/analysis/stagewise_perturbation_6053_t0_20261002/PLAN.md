# Issue #6053 T0 — finite stagewise perturbation diagnostic

## H / T / D / C / U

- **H:** A paired finite stage graph can distinguish contraction, amplification, late perturbation, branch divergence and zero-denominator cases; checkpoints can reset comparable state deviation without hiding a prior branch divergence.
- **T:** Five exact affine stage fixtures with common exogenous disturbances applied identically to matched nominal/perturbed trajectories; A serial propagation, B checkpoint at every stage, C later-only checkpoints. Independently enumerate every stage prefix, typed branch, safety bound, exact matched terminal effect and ratio eligibility.
- **D:** `PASS_METHOD_SCOPED` only if every prefix/state matches independent arithmetic, first divergence remains recorded, common disturbances are not attributed to injected upstream error, zero denominator returns NOT_COMPUTABLE, and checkpoint effects are reported without erasing earlier branch divergence.
- **C:** Heterogeneous discrete GUI transitions may not have a common scalar norm; checkpoint improvement can simply reflect extra observations/resources. A synthetic positive control is not evidence for Agent Interface.
- **U:** Authored affine gains and thresholds; no identified GUI chain, empirical perturbation distribution, task oracle, time/action cost, or controller comparison exists.

## Method boundary

The analogy to Swaroop & Hedrick (1996), [DOI](https://doi.org/10.1109/9.486636), is limited to asking whether a disturbance grows across an interconnection. Their interconnected-system results do not transfer to heterogeneous GUI stages. This T0 uses finite exact arithmetic and only reports a ratio when the injected denominator is nonzero and trajectories remain comparable; branch divergence is typed, never converted into an invented scalar.

## Execution

Source base: `3adec9cdc2cff5ef68f19acd55c5823fcaad26df`; additive package. Construction mutations precede a final freeze; candidate and independent enumerator each run once afterward. Host CPython only; no Docker isolation claim because Docker Engine is unavailable. No model, network, GUI, game, GPU, physical input, or live authority.
