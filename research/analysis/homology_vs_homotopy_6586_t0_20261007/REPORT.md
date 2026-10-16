# Issue #6586 — ordered homotopy words vs homology vectors T0 A01

## Result

**`PASS_REPRESENTATION_BOUNDARY_SCOPED`** for the finite frozen planar fixture. Two obstacles were represented by disjoint rectangles with fixed upward cuts and complete integer-coordinate generator loops. The candidate emitted all 5,461 words over `{a,A,b,B}` through length six; a separate raw-only auditor independently rebuilt each polyline, verified that it avoids both obstacles, reconstructed the ordered cut crossings, and recomputed both the exponent vector and freely reduced word. Audit exited 0 with `errors=[]`.

The bounded exhaustive deck contained 77 winding-vector buckets with more than one distinct reduced word. The central witness was the empty route vs. `abAB`: both have homology vector `(0,0)`, while free reduction leaves the commutator `abAB` nonempty. Under this punctured-plane model, the two are therefore distinct based homotopy classes despite equal first-homology signatures. All 127 one-obstacle words through length six had no such collision. Adjacent inverse cancellation and distinct raw route lengths reducing to the same word behaved as frozen; unfinished, missing-receipt, and stale-topology controls returned `UNKNOWN`.

This confirms a representation boundary, not an agent/controller defect: a homology vector is not a complete homotopy-class identifier for two obstacles. It does not establish that preserving the distinction changes any path choice or task outcome. The 2012 source paper constructs complete invariants for the stated homology classes; this report does not attribute a false claim to that work. [Source paper](https://arxiv.org/abs/1208.0573).

## Mathematical interpretation

The plane minus two disjoint contractible obstacles has the homotopy type of a wedge of two circles. Its based fundamental group is the free group `F2 = <a,b>`. First homology is the abelianization `F2/[F2,F2]`, isomorphic to `Z²`, so it retains the exponent sum around each obstacle but forgets generator order. The commutator `aba^-1b^-1` lies in the kernel of abelianization and is not the identity in `F2`: it is already freely reduced. Appending the same basepoint-to-goal tail to both loops preserves their distinction as fixed-endpoint route classes.

With one puncture the fundamental group is `F1 ≅ Z`, so abelianization loses no order information; the finite rank-one control is consistent with that fact. This standard algebraic argument, rather than the length-six enumeration alone, explains why the collision generalizes within the stated topology.

## H / T / D / C / U

**H:** For two obstacles, per-obstacle signed winding alone may identify homotopically distinct complete routes. The witness was reproduced. No claim is made about controller utility.

**T:** Frozen two-obstacle planar geometry; generator loops around each obstacle; an ordered ray-crossing receipt; bounded exhaustive words; a separate geometry/raw auditor; rank-one and evidence-quality controls.

**D:** PASS for the representation boundary: 5,461/5,461 route rows independently reconstructed; 77 collision buckets; explicit identity/commutator separation; 127/127 rank-one control words; six frozen controls; five effective mutation classes rejected by construction tests. Candidate and auditor each ran once, both exit 0, zero retries.

**C:** If the environment or allowed route family excludes interleavings such as the commutator, or if only homology-equivalent outcomes matter, the richer word may be unnecessary. A nonabelian label does not imply useful navigation progress.

**U:** No visual geometry or crossing sensor, partial-map inference, dynamic environment, path policy, GUI/game, physical movement/release, task effect, timing, safety, or product benefit. The auditor verifies authored coordinates and receipts, not perception. Missing or stale crossing evidence remains UNKNOWN.

## Execution and provenance

Base commit `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`. Candidate raw SHA-256 `b422609df51f5cdfe00dd4b96521b40492bd5a38a4533e65b187c36b71679245`; audit SHA-256 `f3529b5e20a4e5b286e911f8a8f6625ac2a513e2a3938750113fdf29cac21c84`. Both stderr files are empty. Exact source hashes are in `FREEZE.json`; complete package hashes are in `SHA256SUMS.txt`.

Execution used `python:3.13-alpine` digest `sha256:2d9aefe2fef018a7eb2c13064c89c71929800fd2e5dccdbf52ea5da5bb8d929a`, linux/aarch64, OrbStack, network disabled, read-only source mount, 512 MiB and one CPU. No experiment network, model, GUI, external effect, or live authority.
