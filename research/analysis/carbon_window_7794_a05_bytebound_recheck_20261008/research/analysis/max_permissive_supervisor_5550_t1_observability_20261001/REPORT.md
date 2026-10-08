# Issue #5550 T1 — partial-observation boundary

**Disposition: `PASS_T1_SYNTHETIC_SCOPE` (host-only finite-model result).**

## H / T / D / C / U

- **H:** When `ACTED` and `STALE` are indistinguishable, the belief-safe
  supervisor disables `COMMIT` but retains the common safe `REVALIDATE` action.
- **T:** A 15-edge synthetic plant, belief `{ACTED, STALE}`, four controllable
  event types and one independently enumerated raw-only audit.
- **D:** Candidate enabled only `REVALIDATE`; `COMMIT` was disabled. The
  independent auditor agreed on all fields, returned `errors=[]`, and rejected
  all 4/4 preregistered corruptions. The exhaustive oracle found 2 safe edge
  subsets and 1 maximal safe subset. All six frozen tests passed.
- **C:** The model hand-adds a perfect `REVALIDATE` edge from both states;
  progress is therefore conditional on that mechanism existing and working.
- **U:** This establishes only a property of the declared deterministic finite
  model. It does not test real observation freshness, GUI event classification,
  hidden effects, timing, task success, utility, or runtime integration.

## Execution record

- Source main: `e94101a1bd2ad6e3e103088aa4d169c2ad112086`.
- Preregistration commit: `caf560074765b750d24edefc62fe352122dfc952`.
- Frozen commit: `0ba178b573e7e55f60cd929454f02e90513bfa85`.
- Candidate SHA-256: `bc04f837ace58fc1b1bf17e06bed9c84a4296f1655a1679b88cb7f869a8237e4`.
- Auditor SHA-256: `81a83cc02756a59edd7ebce2521682dcbb28ae86f7774dd24daeeda26176d415`.
- Raw SHA-256: `9d6fa40815a876ab483aae747e48f6c82149eb85899fe6f99446cdbdd7e28d86`.
- Audit SHA-256: `7a349a52239f559daf3d084bdbe8c2d57c24cc2f005238082833134e948d509b`.
- CPython 3.14.5, host CPU only. No Docker/OrbStack, network, GUI, model,
  GPU, or shared resource lane was used.

See `FREEZE.json` and `RUN_LOG.md` for source identities and invocation
accounting. The prior T0 formal STOP remains unchanged; this host-only result
does not reinstate or validate its expired container allocation.
