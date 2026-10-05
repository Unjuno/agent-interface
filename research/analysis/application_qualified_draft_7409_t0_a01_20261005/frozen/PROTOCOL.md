# Issue #7409 T0 A01 protocol

## H / T / D / C / U

**H.** On a deterministic, versioned document fixture, native private-draft semantics can preserve concurrent disjoint human and agent edits, surface same-field and read/write dependency conflicts, and refuse shared-backend or external-effect cases before the agent draft changes live state. A direct shared-live comparator can silently overwrite a same-field human edit.

**T.** Use the six authored rows in `cases.json`: disjoint updates; same-field conflict; hidden read/write dependency conflict; a changed live revision with disjoint updates; an isolated UI context whose draft still autosaves to the shared backend; and an external side effect. Compare a direct shared-live patch path with a staged path that creates an app-versioned draft from `r0`, applies an independently authored human commit, checks the live revision and read/write conflicts, then promotes only a conflict-free draft under an explicit promotion flag. Candidate writes one raw JSON result. After candidate exit 0, an independently written raw-only auditor reconstructs each direct and staged outcome from `cases.json`, not from candidate labels. Six output mutations challenge pre-promotion isolation, same-field and hidden-dependency conflicts, revision checking, shared-backend refusal, and external-effect refusal.

**D.** `METHOD_PASS_SCOPED` requires exact independent reconstruction of all six rows; disjoint human and agent edits both present after promotion; same-field and dependency conflicts held without agent promotion; a changed revision checked before any promotion; shared-backend and external-effect cases refused without a draft write; zero agent effect in live state before explicit promotion; and rejection of all six frozen output mutations. Any leaked write, silent overwrite, missing conflict, or executed draft side effect is `FAIL_ISOLATION_OR_MERGE`; missing or unreconstructable rows are `FAIL_AUDIT`. This T0 establishes only behavior of this authored fixture.

**C.** A direct non-modal/background route or ordinary context restoration may avoid live-view interference more simply. A draft route may cost more to review or may conservatively hold cases that a richer application conflict oracle could merge.

**U.** No actual document application, browser, human, model, live view, focus change, production revision system, or external service is tested. The fixture's version, field dependency, backend-isolation and effect semantics are stipulated inputs, not discovered application properties. No user benefit, safe merge in a real app, runtime feature, or safety claim follows.

## Frozen execution

- Issue: https://github.com/Unjuno/agent-interface/issues/7409
- Allocation: `APPLICATION-QUALIFIED-DRAFT-7409-T0-A01-20261005-01`
- Source base: `19a6b723e58ccfd2b8265e88659589ef9223fcc9`
- Image: `python:3.12.12-slim@sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c`; local platform `linux/arm64`, image config ID `sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c`.
- Runtime: OrbStack Docker, one CPU requested, network disabled, read-only container root and source mount, `/tmp` limited to a disposable tmpfs, distinct writable result mount.
- Formal invocations: candidate exactly once; auditor exactly once and only after candidate exit 0; retries 0. A nonzero exit is preserved and terminates the allocation.
- The candidate receives only `cases.json`; the auditor receives that same frozen file and candidate raw output. Both use Python standard library only.
- Result directory: `results/a01/`. No runtime or application behavior is inferred from this finite test.

## Container commands

Run from the repository root after recording the absolute `PKG` path and verifying the source manifest. `OUT` is the package's `results/a01` directory.

```sh
docker run --rm --network none --cpus 1 --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --mount type=bind,src="$PKG/frozen",dst=/src,readonly --mount type=bind,src="$OUT",dst=/out --workdir /src python:3.12.12-slim@sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c python -I /src/candidate.py /src/cases.json /out/candidate.raw.json
docker run --rm --network none --cpus 1 --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --mount type=bind,src="$PKG/frozen",dst=/src,readonly --mount type=bind,src="$OUT",dst=/out --workdir /src python:3.12.12-slim@sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c python -I /src/auditor.py /src/cases.json /out/candidate.raw.json /out/audit.json
```

The first output is the candidate's only formal invocation. Execute the second command only if the first exits 0. Capture stdout, stderr, exit status and raw file hashes without editing either raw output.
