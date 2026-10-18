# A10 source and input freeze

- Allocation: `5309-WITNESS-A10-HOST-20261007`
- Frozen main: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`
- Branch: `research/5309-witness-topology-a10-20261007`
- Runtime: CPython 3.14.5 on macOS host; no container or OS sandbox.
- OrbStack preflight: engine 29.4.0; image inspection failed with the previously recorded content-blob `operation not supported` error. No container was created.
- Construction tests: `test_construction.py` 3/3 passed after retaining and correcting the initial 132-vs-72 expected-count error. The deterministic design materializer ran before this freeze.

SHA-256 (frozen before any formal candidate invocation):

| File | SHA-256 |
|---|---|
| `PRE_RUN.md` | `37c1cab73b9e7ba91b2fbcca14b1bd5106df407a40d5efdcf9a43096c280960b` |
| `README.md` | `21ac0ad2e5850b1ae675f4deafa78b5891ade9d8b87440a630daa0354b560d63` |
| `design.py` | `666c228ecf5c6be0ce7c64258f2212852acf5cbf980f0f5a6dd640d6f935fedb` |
| `candidate.py` | `c0c5483f843c31c15f520a2e9b7e2941c16c3ee0f6fcc0c572f908e5da56bd51` |
| `environment.py` | `cb89ccb001c299fbc8df730719099ea9113a70b7481514477d04c20c6866e257` |
| `auditor.py` | `3befdaba4a7bbb328b7b5395bea9570619fc6f8046c46d8b22c8d73a7cf21fd9` |
| `test_construction.py` | `b4353a3d5317246f2da2b314f8d77eba0d74437dc4c2471dbbe27a36de87e6ab` |
| `candidate-input.json` | `99920a89bd476492206b59b38fdebd79c8475a5e0d3fd3c6129e99fb6609c72e` |
| `oracle.json` | `5e4ce0ecda8b0124850d218f20773815a232dcbf432c5f790968eb38bbb62add` |

No source, input, oracle, gate, or command changes are allowed after this point. Run candidate, environment, and auditor exactly once each in the order specified by `PRE_RUN.md`; retain any failure without retry.
