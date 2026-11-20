# Construction record — homology/homotopy T0 A01

- Frozen source main: `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`.
- Two disjoint closed rectangular obstacles are embedded in the plane; each generator loop approaches from below, encloses exactly one obstacle, crosses only its corresponding upward ray, and returns to the common basepoint. A shared tail to the goal is appended after each based loop word.
- The ray crossing direction is fixed as the positive generator direction for both obstacles. Inverse letters use the reversed complete polyline, so order and signs are obtained geometrically, not copied from the intended word.
- Candidate enumerates every word of length 0–6 over four letters (5,461 total) and all one-generator words through length six (127 total). The independent auditor implements word normalization differently and reconstructs each polyline's crossings separately; it also rejects obstacle intersections.
- All seven construction tests pass in the pinned container. Five mutation classes are used in the construction suite. No construction/formal retries were required.
- The symbolic interpretation is bounded by the frozen punctured-plane topology. The finite deck itself cannot establish perception or a route policy.
