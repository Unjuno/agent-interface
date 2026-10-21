# Preformal construction record

Allocation under consideration: `SELECTION-AWARE-PARTIAL-IDENTIFICATION-5681-T0-20261005-01`. All records below precede its freeze/first formal candidate invocation. They are not formal candidate or auditor outputs.

## Host source tests

- Windows CPython 3.11.9, host CPU.
- `python -m unittest -v test_method`: 12 tests passed.
- `python -m py_compile candidate.py audit.py test_method.py`: exit 0.
- `git diff --check`: exit 0.
- TDD first red run caught the missing interval/decision outputs; the stub candidate and stub auditor produced the expected assertion failures. An early run also exposed a test expectation error in completion accounting (the first case has 2 unknown labels, thus 4 completions) and a representation mismatch for `0/1`; both were corrected before freeze.

## WSLc mount smoke

One separate construction-only container ran the cached image with the planned one-CPU, 128 MiB request, `--network none`, a read-only `/src` bind mount, a distinct writable `/out` bind mount, and an 8 MiB temporary filesystem. It read the eight-case JSON, reported Linux `x86_64` / CPython `3.12.15`, and exited 0. It did not import or invoke the candidate or auditor and wrote no candidate result.

WSLc printed: `Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` The container inspect showed the configured `NanoCpus=1000000000`, `Memory=134217728`, network `none`, `/src` `ReadWrite=false`, `/out` `ReadWrite=true`, and exited status 0. This does not prove effective memory or swap enforcement.

Container identity: `5e01314f12d7503f09c18e5815c467f86d4220a11e300423a416bf5fdbb634d6`. The first PowerShell cleanup wrapper failed after the container had exited because `-Raw` was accidentally passed as a `Join-Path` component; no candidate/auditor command ran. A corrected read-only ID lookup, `wslc inspect`, `wslc remove <id>`, and subsequent `wslc list --all` verified that this construction container was removed. No other container was changed.

Formal allocation counts before freeze: candidate 0; auditor 0. No formal invocation occurred in construction.
