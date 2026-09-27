# Exact harness source note

The disposable A2 harness source SHA-256 at execution was:

- `helper.py`: `b7fc69dbb63ff31ed9bdb7787bd44a368772923389724d9404c2ed9469ca5171`
- `experiment.py`: `ecfc8bb980981f47e383583ecff11add3b0d07e1d3f1fdc051c32b3caa318db4`

`helper.py` is retained byte-for-byte in this namespace. The monolithic `experiment.py` is not promoted as reusable source because the first formal invocation was terminated by the outer 45 s execution envelope before aggregate serialization. Its exact hash is retained for provenance; no successor may treat the partial execution as a scientific sample.

The compact `CONSTRUCTION.json` records only the construction predicates needed to establish that #1537's raw-PTY delivery stop did not recur. Full local timing rows were not promoted as formal evidence.
