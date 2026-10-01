# Issue #6102 T0 result

The frozen exact enumeration covered all 5,461 words over `open(A)`, `open(B)`, `close(A)`, `close(B)` up to length 6. The independent audit matched the candidate: 51 well-nested complete traces; 306 balanced-depth traces that a flat depth-only gate would accept despite wrong parent identity; and zero disagreement between the bounded depth-3 FSM and literal stack on the declared domain. 432 traces exceed the depth-3 cap and return UNKNOWN. Result: `PASS_METHOD_SCOPED`.

The initially constructed candidate (before freeze) incorrectly accepted unfinished nonempty terminal stacks; it is preserved in `CONSTRUCTION_FAILURE.md` and is not formal evidence. The corrected frozen source passed the independent audit. This result establishes only the finite semantics above. It does not establish that real GUIs expose reliable nested call/return events, that arbitrary-depth identities fit a finite alphabet, or that a stack is preferable to an equally correct bounded FSM. No runtime, safety, task-effect, or product claim follows.

Docker Desktop's backend processes were present, but the configured `desktop-linux` Engine API did not return to `docker ps`/`docker version` within 10 seconds. Because this is exact CPU enumeration with no OS/app/model dependency, container execution was not methodologically required; no container run is claimed.
