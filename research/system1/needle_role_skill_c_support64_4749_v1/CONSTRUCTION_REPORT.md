# Construction report — seed 7865001

One preformal paired synthetic run used local Docker image needle-pilot05:local (sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e, linux/amd64). It is not part of the formal block and supports no population inference.

Independent audit: CONSTRUCTION_AUDIT_PASS, zero errors. Two fresh loaders per arm accepted each inert package and matched all role predictions; graph and corruption controls passed. The 16-row C support is an exact prefix of the 64-row support. A/B are exactly unchanged.

| Role | control16 | treatment64 | paired delta |
| --- | ---: | ---: | ---: |
| A | 0.965820 | 0.965820 | 0 |
| B | 0.928223 | 0.928223 | 0 |
| C | 0.954834 | 0.962646 | +0.007812 |

This single C delta is below the formal preregistered >=0.01 mean gate; the gate is not relaxed. Formal seeds remain unconsumed.

The current offline Docker suite passed 10/10. Earlier host/container attempts passed 7/9 because two test fixtures incorrectly assumed a /raw mount. Tests were changed to use fixture paths relative to the test file; a fail-closed formal preflight test was also added. Trainer, loader, auditor, construction data, and formal seeds were untouched. Full rerun passed, including independent deterministic retraining. PyTorch warns that NumPy is absent; tested CPU paths do not use it and no dependencies were installed. An initial Docker inspection template referenced an absent metadata field; corrected inspection succeeded without container state changes.

Limits: synthetic fixture only; no online learning, real user data, external model provider, GUI, actuator, natural-transfer or production claim.
