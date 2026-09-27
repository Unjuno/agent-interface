# Local NumPy model target-position support (successor #2564)

`PASS_TARGET_POSITION_SUPPORT_SCOPED` under the preregistered pooled gate. Five paired seeds and two held-out translations show a highly location-dependent effect: the treatment accepted 200/200 positives at `(8,15)` but 0/200 at `(20,25)` (all 200 yielded there). It retained 200/200 base acceptance and made 0 false ACCEPTs over 600 negative cases. Independent raw-only audit: complete, `errors=[]`.

This is a synthetic CPU-Docker experiment, not a real GUI or general visual-robustness result. The full limitations, per-location decision breakdown, and handoff are in [`results/REPORT.md`](results/REPORT.md); the preregistration is [`FREEZE.json`](FREEZE.json), and the machine-readable outcome is [`results/RESULT.json`](results/RESULT.json).

