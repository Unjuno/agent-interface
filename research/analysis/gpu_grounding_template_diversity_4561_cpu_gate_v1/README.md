# Issue #4561 — CPU renderer and coordinate-oracle gate

This additive, CPU-only construction study checks deterministic local raster
rendering, geometry-derived coordinate labels, family-level split integrity,
and strict schema validation. It does not retry the predecessor CUDA STOP,
train a model, score GPU behavior, or decide the template-diversity hypothesis.

## H / T / D / C / U

**H.** Frozen template-family specifications produce repeatable pixels and exact
field/submit centers; family identity and source hashes remain disjoint across
the declared train/held-out split.

**T.** Allocation `gpu-grounding-template-diversity-4546-successor-01-cpu-gate`.
Twelve authored 1280x800 synthetic form families, each with four fixed variants;
families 01–08 are training and 09–12 held out. No variants are used for model
training in this CPU gate. Pillow drawing is local only.

**D.** Pass if a second render is byte-identical for all 48 images, every label
equals the geometry oracle and lies at a 32-pixel cell center, source hashes are
unique, split families do not overlap, the strict main validator accepts every
candidate, and deliberately corrupted coordinates are rejected by the auditor.
Any unmet condition is FAIL for this construction gate. No CUDA/formal call.

**C.** Python 3.11, Pillow 10.4.0, fixed integer geometry and RGB drawing only;
no external data, augmentation, network, GUI or GPU. This does not establish CNN
learnability, CUDA determinism, or transfer to real interfaces.

**U.** Whether the successor's CNN construction is deterministic on CUDA remains
unresolved; whether synthetic template diversity improves held-out grounding
also remains unresolved.

Run `python render_audit.py` from this directory. It writes the deterministic
manifest and PNG evidence into the supplied output directory (default `out/`).
The tracked source template is frozen before the local execution.
