# #5826 A02 result — WSLc container-transfer replication

## H / T / D / C / U

**H.** The byte-identical A01 oracle-blind candidate and separate auditor can execute in a WSLc container and reconstruct the same finite 18-opportunity / 72-row result.

**T.** After source hash checks and an import-only construction smoke, candidate ran once, auditor ran once, and the five frozen corruption controls ran once as separate network-isolated, auto-removed WSLc containers. No model, GUI, OS input, external service, GPU, Docker Desktop daemon, or image pull was used. The exact command and image identity are frozen in [PREREGISTRATION.md](PREREGISTRATION.md); full container output is retained in `out/`.

**D. `PASS_WSLc_TRANSFER_SCOPED`.** Candidate exit 0; candidate data records 18 opportunities and 72 channel rows and identifies `Linux-6.18.40.1-microsoft-standard-WSL2-x86_64-with-glibc2.41`, `x86_64`, Python `3.12.14`. Independent audit exit 0 reconstructed 9/12 faults (0.75), all-channel misses F02/F04/F08, runtime false report N16, verifier UNKNOWN N18, and runtime/watcher naive / Chapman estimates 7.5 / 7.0 against the fixture truth of 12. Mutation controls rejected 5/5: omitted row, duplicate row, mislinked event, UNKNOWN coerced to negative, and oracle-truth flip. All five sources match their frozen SHA-256 values. Candidate stdout SHA-256 `a2a0275dcf86e6e0f356a96f2ee2d3646b74f28c817c96914c40cb5a5f3dd6ad`; candidate JSON SHA-256 `70810da437e59e770c024341fef6b0e16abf2171000f86cb0b85317e5a3df915`; auditor stdout SHA-256 `9fbca995c8925b7574a3141ff23b9298a6b46dc4aaab8c6a139c65e20c132aeb`; mutation stdout SHA-256 `fd6b2e5b71b46f6a56e72575925d069c5fba61cdd688f0aa7b8ebef709c41cd9`.

**C.** Windows 10.0.26200.9550; WSL 3.0.1.0; WSLc 3.0.1; kernel `6.18.40.1-1`; linux/amd64 `python:3.12-slim`, repo digest `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, local image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`. Each scientific container requested 0.25 CPU, 256 MiB memory, no network, a read-only source mount, and distinct output mount (auditor/mutations read-only). WSLc emitted: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` No resource-enforcement inference is made. Containers were invoked with `--rm`; post-run inventory showed no A02 container names.

**U.** This qualifies only execution/reproduction of one deterministic synthetic fixture in this WSLc route. It does not prove effective CPU or memory limits, Docker/OrbStack equivalence, production ascertainment, actual unseen-fault prevalence, safety, or user benefit. A01 host PASS and OrbStack STOP remain unchanged. The auditor's legacy output labels are retained literally: `PASS_METHOD_SCOPED_HOST` / `HOLD_CONTAINER_TRANSFER (not exercised)`. Inspection confirms those are unconditional strings after the audit call; A02's container runtime provenance is established separately by the candidate's Linux environment record and captured WSLc invocation outputs. This label inconsistency is a reporting defect, not an audit-data mismatch.

## Reproduction

Use the exact frozen source/image/commands in [PREREGISTRATION.md](PREREGISTRATION.md). Source copies are included under `source/`. Do not overwrite the retained candidate output or describe this fixture as a live/system incident-rate estimate.

## Lineage

This is distinct from the A01 host-only candidate/audit result and its OrbStack container-runtime STOP, all retained unchanged in Issue #5826 and draft PR #8389. A02 answers only whether the exact frozen package can run in the available WSLc container route. Publication base: main `bfcc14e08fbfe5f2f04cd0237d13559e5d62538b`; source package ref: PR #8389 head `6086879eac550ed0fa05175011d8d39602e55393`.
