# Local Windows validation

Candidate 51549cba72d727ba2b787c4e9673b86eeb462906 has tree eb0abc591512f91db7ab7b2cdc6c5854e9d1c0c2. A parentless validation commit 10d43e70b9284589f49fe7e291530a3fb3c6666f has the exact same tree. A self-contained Git bundle transferred this snapshot to a fresh Windows Git repository. The runtime artifact provenance correctly names the snapshot commit, not the candidate commit.

The first UNC partial-clone transfer failed on unavailable promisor objects. Full snapshot checkout without long-path support then failed on unrelated long research paths under the deep local workspace. Both failures are retained. Checkout with command-scoped core.autocrlf=false and core.longpaths=true succeeded, and `git status --short` was empty before tests. `git rev-parse HEAD^{tree}` matched the candidate tree above. No evidence bytes were rewritten to handle path length.

The migration verifier passed on this Windows checkout: 48 image SHA-256/Git-blob identities and 21 original study files unchanged. The runtime-cli-v1 workflow test list plus runtime.distribution_v2.test_distribution ran 109 tests: OK, 2 skipped. A separate portable build completed; artifact size 209109, SHA-256 6f223467b4b4f713e7db716c1a439a7b317e0186a9b8486d47a10c46dff1cd11. Its doctor returned runtime_available=true and Win32 backend available; it is diagnostic, not GUI task success.

An earlier Windows-on-UNC run returned 5 errors among 109 tests because Git rejected repository ownership; its process-scoped safe.directory retry passed all 7 distribution tests. Those local logs remain in results-local. The definitive clean-Windows-checkout run above requires no safe.directory exception.

Subsequent candidate edits add only migration validation records and workflow filters/Windows long-path configuration; runtime and original study bytes are unchanged. Hosted Linux/macOS/Windows checks remain a separate gate. No scientific allocation was rerun and no model/input-performance claim follows.
