# Issue #5318 - construction result and disposition

Allocation `semantic-serializability-fsm-r0-20260930-01`; intake main `c4735cfd27bfca057d9c1fca9a7ea19866f77259`; branch `research/semantic-serializability-5318-20260930`.

## Result

One candidate invocation ran in OrbStack linux/arm64 using cached image ID `sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db` (Python 3.12.10), with `--network=none --read-only --cpus=1 --memory=512m --pids-limit=32`; candidate exit 0. A separate auditor container invocation exited 0. No model, GUI, external input/effect, authority, or network was used.

Raw SHA-256 `c497361ec8d76d5643bdb8b622d17c8b0b60dc0cfbe5dca793e8163edb7602cd`; saved initial audit SHA-256 `455ffb80dd15117dcc0fd6d10424bffc7df8fd36d782c17597f2b2ff84873199`. Frozen candidate SHA-256 `fccd74d603b1d8c72bba3609bc865f0e42b2124e07b023bc3003fa66df21e10c`; frozen initial-auditor SHA-256 `880359b7670c4a3d19338819d39345c1411f70feda55bc26259e1c9de4a2e1a5`.

Five fixed cases executed. The semantic gate parallelized two pairs: the known-disjoint case and the hidden-read case. The latter has different legal serial outcomes (`y=1` vs `y=2`) but the concurrent run does not retain a schedule-order identity. Its declared footprint omits the actual read, so the gate also admits it. Global serialization parallelized zero; RAW_COALESCE parallelized all five. Same-key increments were a declared write conflict but converged to the same final state, so conflict is not itself proof of non-serializability. Unknown footprint returned `UNCERTAIN`.

## Integrity correction / disposition

The initial independent auditor's saved `errors=[]` is **not accepted as a valid audit**. Post-run raw review found that candidate-provided `oracle.concurrent_matches_serial` says `true` for the hidden-read case by comparing the observed state only to a fixed B-then-A execution; it does not establish which concurrent order occurred. The auditor did not recompute this boolean correctly and the raw schema lacks a concurrent schedule identity. The 3 local audit tests confirm the saved raw outcome and preserve the hidden-read counterexample, but do not repair that formal auditor defect.

Disposition: `HOLD_AUDITOR_AND_SCHEDULE_PROVENANCE`. This is not a PASS for the #5318 hypothesis and not a runtime claim. Preserve the candidate raw and initial audit bytes unchanged. Do not rerun this one-shot allocation. A fresh successor allocation must freeze a schedule ID/linearization witness, independently compute serializability from that witness and actual operation read/write sets, and include this hidden-read miss as a counterexample/control.

## H/T/D/C/U

- **H:** partially challenged: known conflicts are serialized, but an omitted hidden read passes through and causes an unresolved order-dependent outcome.
- **T:** one deterministic five-case synthetic OrbStack construction run plus a separate raw-auditor invocation; no retry.
- **D:** formal acceptance not met. Saved audit is held for the auditor/schedule-provenance defect; no PASS/FAIL on the broad population hypothesis.
- **C:** synthetic finite cases only; no real side effects, model, GUI, input, network, or authority.
- **U:** no generated workloads, trustworthy real-world footprint extraction, fairness/starvation, concurrency throughput or latency measurement. Concurrent schedule identity was not retained. Container image OS/architecture was confirmed as linux/arm64, but its local Python base tag's metadata was malformed; execution used exact cached image ID and runtime version was observed directly.

Local post-result CI: `python3 -m pytest -q` => 3 passed; `python3 -m py_compile candidate.py audit.py test_audit.py` passed. These tests validate the reported finite raw and detect the hidden-read limitation; they do not supersede the held formal auditor.
