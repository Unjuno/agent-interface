# Issue #5836 corrected T0 successor result

Allocation `trusted-confirmation-5836-t0-successor-20261001-01`; exact main at freeze `45395880f873f1592bc188a37471d8380535e1ec`. This is a new allocation after the predecessor's invalid auditor oracle and observed stateless-replay defect. The first result remains preserved at the sibling `research/5836_trusted_confirmation_t0/` path.

## H/T/D/C/U

- **H:** Independent-channel request-bound single-use receipts can refuse surface forgery, expired or previously consumed nonce, target/principal substitution, revocation, and ambiguous-delivery retrial while allowing one exact matched approval and explicit denial.
- **T:** One deterministic 10-row comparison in three arms (page/model text approval; request-bound but replayable receipt; independent-channel consumed-nonce receipt) with separate candidate and raw-only auditor. Docker network disabled; read-only source/root; 1 CPU, 256 MiB, 64 PIDs. No model, GUI, human subject, payment, privilege elevation, credentials, or real application effect.
- **D:** `PASS_METHOD_SCOPED` iff exact raw rows match the independent oracle and all five mutations reject. Candidate and auditor each ran once; both exited 0; no retries.
- **C:** A simpler broker-bound boolean plus exact effect digest might suffice. This finite fixture cannot establish that the production trust boundary is truly independent.
- **U:** All channel authenticity/provenance is simulated; no real human comprehension, OS/hardware trusted path, accessibility, coercion resistance, or effect is measured.

## Result

`PASS_METHOD_SCOPED` for this finite synthetic fixture: all 10 rows matched; the trusted arm authorized only the exact `valid_match` row (one attempt), rejected a page/model forgery, expired receipt, pre-consumed replay nonce, target/principal substitution and revocation; the lost-response row consumed one attempt and did not retry; explicit denial produced no attempt. The request-bound but replayable comparator permitted two attempts in both replay and ambiguous-delivery cases. Five of five planted output mutations were rejected by the independent auditor.

This is semantics/construction evidence only. It does not prove a real trusted UI/channel, human approval quality, correctness of a consequential action, or integration with Agent Interface admission. No product code changed.

## Exact environment and artifacts

- Local Docker Desktop Engine `29.8.0`, context `desktop-linux`; local image already present, no pull: `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, image ID same digest, `linux/amd64`.
- Candidate command: `docker run --rm --network none --read-only --cpus=1 --memory=256m --pids-limit=64 --mount type=bind,source=<allocation>,target=/src,readonly --mount type=bind,source=<allocation>/results,target=/out <pinned-image> python /src/candidate.py /out/raw.json`.
- Auditor command: same isolation/bounds, source and `/out` read-only, `python /src/audit.py /out/raw.json`.
- Candidate exit 0; auditor exit 0. Raw-only stdout is preserved verbatim as `results/audit_stdout.json`.
- Candidate SHA-256 `840f3ac798b3f5686ded2efacdcc4aafe6ab8c7b88d4e838cf9ea625fb080857`.
- Auditor SHA-256 `94d84da4f244d50a538a9cc85d27f5d54dbe97ddd5bca7f533facdea9d79b37b`.
- Plan SHA-256 `f4775f78abc279273cd9f406047a7b87fb246429aea3878512b7cfca2957e1f7`.
- Raw candidate JSON SHA-256 `685e2fc8fdd8e85805a14eaa9c849de2f6ed48eb19a4994bd30c7d94d4577f68`.
- Auditor stdout SHA-256 `b08c352d06d8aca7a1e89fe1daa16dbd678b3a506de97264b1db19c91b3a692`.

The first-allocation STOP and its flawed oracle remain immutable and are not counted as a successful trial or pooled with this successor.
