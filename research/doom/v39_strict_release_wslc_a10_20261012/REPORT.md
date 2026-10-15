# V39 strict release receipt: WSLc replay A10

**Result:** current-main snapshot fails at test-module import because the stricter known-empty release helper is absent; PR #8835 candidate passes 7/7 focused tests in both normal and optimized CPython. This independently reproduces the release-readiness distinction inside WSLc using the current PR head and its actual current-main base.

The candidate requires explicit empty `keys_unknown` and `key_state_errors` fields in addition to verified empty keys/buttons. Its startup preflight requires the measurement session (V15 receipt producer), because the ordinary V10 path cannot prove those fields. The suite checks the helper, stale-cover recovery composition, and rejection of the default session before output creation or child launch.

The baseline run exited 1 before unittest collection: the candidate test module's AST precondition found that current main did not define `terminal_release_is_known_empty`. This is an expected regression contrast; it is not counted as a set of per-assertion failures. Candidate normal and `-O` runs each completed 7 tests successfully.

Source commits and blob identities are in `inputs/source-manifest.json`; the byte-exact source bundle and raw command outputs are retained here. The container used the cached pinned Python 3.14.8 linux/amd64 digest, no network, one requested CPU, 512 MiB requested memory, UID 65534, and a read-only source mount. WSLc reported that swap limits are unsupported on the host; no swap-limit claim is made. The container inventory was empty after execution.

## H/T/D/C/U

- **H:** Current main lacks this strict-release gate and candidate startup source gate; the PR candidate enforces both in the focused construction path.
- **T:** Byte-pinned main/candidate controller and three candidate test modules, run once per source/mode in WSLc, with source/base/head identities fixed.
- **D:** Main import fails on missing helper; candidate passes 7/7 normal and 7/7 `-O`.
- **C:** The main run stops at the module AST assertion, so it does not quantify the legacy code's behavior over every candidate case. Existing PR evidence separately records the focused old/new assertion contrast.
- **U:** This only validates deterministic Python receipt/preflight behavior. It does not establish producer authenticity, exact physical key-up timing, live input state, game effect, recovery benefit, threat response, or MAP01 completion.

The first audit script failed because it expected the assertion message in the unittest traceback; that initial failure is preserved in `AUDIT_ATTEMPT1.json`. The auditor was corrected to match the traceback source line and then passed without rerunning the experiment.

No formal/live allocation was started or consumed, and this construction run does not close [Issue #59](https://github.com/Unjuno/agent-interface/issues/59).
