# Issue #3690 — Docker validation of current typed auditor

Disposition: `PASS_PINNED_LINUX_AMD64_CONTAINER_VALIDATION_SCOPED`.

## H / T

The current typed audit candidate at PR #3683 head `de9acd02b50fac4e9b8c46ed961d923181cbbece` should accept the byte-bound predecessor baseline, reject its frozen adversarial mutations, and produce byte-identical direct-function and CLI results in a pinned isolated Linux/amd64 Python container.

I used the existing frozen source/evidence at that exact commit; no code in PR #3683 or its branch was modified. The test suite ran once in one fresh container. The documented raw-only CLI ran once in a separate fresh container. Both used the exact image reference `python@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, `--platform linux/amd64`, `--network none`, read-only root, and `/tmp` tmpfs. The source mount was read-only; only the separate audit-output mount was writable for the CLI invocation.

## D / observed result

- All **5/5** current unittest methods passed. These cover original-byte binding, prior controls, contradiction/noncanonical mutations, paired raw/freeze substitution, and direct-vs-CLI parity.
- The separate raw-only CLI returned `PASS_OFFLINE_STRUCTURAL_AUDIT`, `errors: []`; all **21/21** committed mutation controls were rejected.
- CLI output SHA-256 is `e2ac7b32c1da563cbcd3cbea285ac5ace4f98d43b3cb9ea046d2bf6c1adbbbc0` and `cmp` was byte-identical to the candidate's retained `evidence/hardening_audit.json`.
- Exact tested source/evidence hashes and container settings are in `source-manifest.json`; command output is retained in `tests.txt` and `hardening_audit.json`.

## C / scope and platform note

This was a Python-only audit validation with no X11, GUI, input, model, or XRes formal allocation. The Docker engine is OrbStack 29.4.0 on an ARM64 host; the frozen Python image ran as Linux/amd64 (the container reported `x86_64`, Python 3.12.14). Thus this validates the requested pinned Linux/amd64 container behavior, but not Docker Desktop-specific host integration or native x86_64 hardware behavior.

## U / limits

Twenty-one finite mutation controls do not prove arbitrary audit soundness and do not revalidate the underlying XRes race or Issue #3675 runtime experiment. Those original artifacts remain unchanged. This closes only Issue #3690's scoped container-validation rung.
