# Environment selection

The fixture is a deterministic analytic renderer and finite CPU controller comparison. No OS, GUI, human, model, runtime, GPU, or external service behavior is part of the claim. The candidate reads/writes only package-local files and uses Python standard library. A container boundary would not test an asserted property, so this A02 is host-CPU-only; this does not claim container portability or isolation.

Exact Python/platform, command times, stdout, exit statuses, output sizes, and SHA-256 values will be recorded in `FORMAL_RUN.md` after the single frozen candidate and audit invocations. Preserve the first outcome; no formal retry is allowed.
