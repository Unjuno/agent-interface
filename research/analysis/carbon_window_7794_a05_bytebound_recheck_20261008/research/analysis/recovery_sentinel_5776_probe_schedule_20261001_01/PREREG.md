# Issue #5776 — probe schedule/amplitude construction experiment

## H / T / D / C / U

**H:** In the authored queue fixture, fewer probe pulses and/or lower amplitude can reduce probe-created losses on no-loss mechanisms, but may also remove the median loss-onset advance seen under stronger repeated probing. The decision object is the joint dose/schedule tradeoff, not “best” tuning.

**T:** Exhaustively evaluate the fixed Cartesian grid of 14 amplitudes `[1,2,3,4,6,8,12,16,20,24,28,32,36,40]` units and seven schedules: `[16]`, `[32]`, `[48]`, `[16,32]`, `[16,48]`, `[32,48]`, and `[16,32,48]`. For each of the 98 cells, run all 3 loads × 5 mechanisms × 6 phase IDs with matched probe/no-probe arms (90 pairs; 180 arms; 96 ticks/arm). The existing authored loss rule and workload are held fixed. This is a separate, host-only construction experiment; allocation-02 remains terminally STOPped, and no formal candidate/auditor allocation is reused.

**D:** Candidate emits the ordered 98 × 90 endpoint ledger and per-arm event commitment hashes. A separately invoked auditor, implemented without importing the candidate or prior runner/auditor, reconstructs every tick from the frozen equations, verifies each event commitment and endpoint, and recomputes the joint metrics. Construction audit PASS means exact reconstruction only. Report the full frontier of median target advance versus control-created losses and pulse count; do not select a deployment threshold or call any point safe.

**C:** A no-probe arm is matched on load, mechanism, and phase. The fixture's 18 target pairs and 54 total no-loss-control pairs per schedule remain fixed. Mechanism labels and event rules are authored; no stochastic inference or external prevalence is attempted.

**U:** Host CPU only because the OrbStack/Obstac lane is reserved by another task and the shared resource gate remains unresolved. This does not establish container execution, field safety, adaptive policy value, external validity, false-alarm probability, or a safe probe dose. The event ledger is compact: it commits to each reconstructed per-tick trace with SHA-256 but retains endpoints/commitments rather than every tick as raw bytes.

## Frozen execution

Source is this additive package plus the unchanged source fixture and candidate simulator in `../recovery_sentinel_5776_probe_intervention_t1_20261001_02/`. Run candidate once to a fresh `raw.json`, then run the independent audit once. Any output-path collision is STOP; no retry or outcome-driven change to the grid. Main is the branch base recorded by Git ancestry; this is not a formal allocation freeze.
