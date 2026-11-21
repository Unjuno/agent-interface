# Research Preview archive fixture mode check — 2026-11-21

## Scope

This finite check uses current main `f9d55130ed6f591c4f478c3b81b210f9a7978b61`, source `release/preview_bundle_v1/test_build_preview.py` blob `e8c3ad14342a0e74b13bcc61f7a84a257b106eb5`. It changes only a synthetic Git fixture in the test; no runtime/release implementation, frozen RC1 source, dependencies, provider, live target, or shared WSLc allocation was touched.

## Baseline

On Windows Python 3.11.9, the unmodified test failed 1 of 4 cases in both normal and optimized mode. The deterministic archive test rejected executable launcher modes. The fixture called `Path.chmod(0o755)`, but with Windows Git's filemode handling both `.sh` fixture entries were committed as `100644`. By contrast, the repository release launcher entries are recorded as `100755` in Git.

The same unchanged tests on Ubuntu WSL Python 3.12.3 passed 4/4 in both modes. This locates the issue to the Windows synthetic-fixture setup rather than the RC archive builder itself.

## Candidate and result

The candidate explicitly sets the two fixture launcher index modes using `git update-index --chmod=+x` after `git add`. On Windows Python 3.11.9 and Ubuntu WSL Python 3.12.3, the candidate passed all 4 tests in both normal and `-O` mode. Raw stdout/stderr and exit codes for baseline and candidate runs are retained here. `conditions.json` pins the source and environment; `SHA256SUMS` covers packet contents.

The change is test-fixture portability only. It does not establish Research Preview acceptance, live GUI behavior, provider behavior, or any Issue #57 integration/efficiency gate. The frozen RC1 branch and Issue #58 supported-host sequence remain unchanged and open.
