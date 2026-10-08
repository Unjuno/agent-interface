# Primary caller snapshot and typed-control evidence: current-main recheck

Date: 2026-10-08 JST

## H/T/D/C/U

- **H:** A primary caller must validate the arguments actually admitted for a call; malformed release/control containers must not count as neutral input or valid negative evidence. Caller-supplied attribution must remain explicitly non-authoritative.
- **T:** Recompose the stacked #7071/#7274/#7279 rescue candidate onto current main, run the host integration suite with a fresh evidence root, and recheck repository indexes. Preserve historical experiment archives without replaying their producers.
- **D:** Latest composed main `b52e37574debe61196b951624a4a0e06c67ac829`; candidate merge head before this report `157b7765adbc08eac36a25eb316105af00f8e79b`. Current PR #8367 contains 251 changed files relative to that main, including the original #7071 request/control evidence subtrees and later method-snapshot/attribution work. Original #7071, #7274, #7279, and parallel successor #8351 remain untouched.
- **C:** `node --experimental-vm-modules --test runtime/host_v1/test_*.mjs` with a fresh `PRIMARY_FAILURE_EVIDENCE` root: 416/416 PASS, 0 failed/skipped on Node 24. The first local invocation omitted this required environment variable and produced expected test-setup failures; the corrected invocation completed successfully. Workspace index: 161 directories PASS; strict analysis index: 777 result directories PASS. Full `git diff --check` is not clean: it reports CRLF line endings in preserved files from the original rescue. Source bytes were not normalized; the exact test output is retained in `results/host_native_suite/`.
- **U:** This is scoped host-suite evidence, not physical GUI/input, live MCP task effect, provider accounting, formal proof, security review, or production adoption. PR #8367 still lacks required nonauthor review and its review decision is empty; its current-head GitHub checks are from the older head, so they must rerun after publication. Related PR #8351 is a parallel, non-ancestor successor with overlapping evidence; keep both and the original branches until the owners/reviewers resolve the integration path. No main merge or branch deletion is authorized by the recorded gates.

## Commands

Exact successful test command and index checks are listed in `COMMANDS.txt`. The host suite log is captured alongside it. No historical producer or browser/GUI experiment was rerun.
