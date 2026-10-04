# WSLc native suite A08 — formal result

Disposition: **PASS**. This is a bounded verification that the frozen integration suite can run in a WSLc container without Docker Desktop. It does not establish project-wide Docker removal, performance improvement, or effective memory enforcement.

## H/T/D/C/U

- **H:** The exact frozen source tree's complete 205-test native integration suite runs successfully under WSLc after scoping Git's safe-directory exception to the read-only mount at `/src`.
- **T:** One build and one candidate run; no retries. Protocol and harness suites ran once each.
- **D:** Exact sparse Git checkout at commit `25700c9f68e9937fc1057a5da91d14c3971bb2b6`; 2,144/2,144 files and 10,634,390 bytes verified; all 54 runner target mappings resolved; working tree clean; four output log digests independently rechecked.
- **C:** WSLc 3.0.1.0, kernel 6.18.40.1; pinned base `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; Git `1:2.47.3-0+deb13u1`; one CPU, requested 512 MiB, network disabled, UID/GID 65534:65534, source mounted read-only, output isolated. Image ID `sha256:1b4a8bd7c0fe372cc0cafa74af433b8ae1f73f1bee0f11a028f126b08b2c128a`.
- **U:** WSLc warned that swap/cgroup memory-limit capabilities were unavailable; memory was reported limited without swap. Therefore effective memory enforcement is unverified. No Docker Desktop comparison, speed/memory benefit, concurrent workload behavior, or broader project migration was tested.

## Results

Preflight: `PASS_PREFLIGHT`. Build: exit 0. Candidate: exit 0. Protocol suite: 63 tests, exit 0, 77.984 s. Harness suite: 142 tests, exit 0, 44.765 s. Total: **205/205 passed**, zero errors. Candidate wall time was approximately 123 s.

The prior A07 run had 8 distribution/archive errors because the non-root process treated the read-only `/src` checkout as dubious ownership. A08 changed only the experiment Dockerfile by adding the scoped system setting `git config --system --add safe.directory /src`; A08 then passed. This does not alter project source.

Independent audit: `AUDIT_MATCHES_PASS`; zero source blob mismatches; all four output log hashes match; exit codes and test counts match; exactly one scoped safe-directory setting found.

Prior failed/stopped attempts remain immutable and documented in issues #5085, #7342, #7357, #7361, #7363, #7368, and #7369. Successor verification: #7372. No product changes are proposed by this evidence-only PR.
