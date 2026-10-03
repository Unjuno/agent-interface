# Qualification for unadopted #6101 source snapshot

This directory preserves three exact files from remote branch
`integration/explicit-stopped-observe-20261001` at source tip
`f797619abb89dacc9c5842edba63e81674bb8db5`:

| File | Source Git blob |
| --- | --- |
| `runtime/host_v1/README.md` | `b26baaa2be93cf1db0a79208eabdd387fd3a487a` |
| `runtime/host_v1/primary_caller.mjs` | `18494baec2d45a5d3e214e32ff965e98547d0814` |
| `runtime/host_v1/test_primary_caller.mjs` | `6df5d08c581d80a6df8ec0ee55fd92816bbed88d` |

These files contain the historical `observeAfterStop()` and
`resultsAfterStop(callId)` proposal. They are an archival source snapshot under
`runtime/results`, not executable production code. The current main runtime was
not modified or validated by this snapshot.

## Local check and its boundary

An initial test invocation from only these three copied files stopped during
module loading because `test_primary_caller.mjs` imports the unchanged sibling
`relay_host.mjs`. This was an incomplete-checkout setup failure, not a test
failure. The exact `runtime/host_v1` subtree was then extracted from the source
commit, and `node --test test_primary_caller.mjs` passed 25/25 tests on Node
v26.7.0. This confirms only the historical source/test pair with its original
sibling files; it is not a current-main integration test, container/WSL test,
GUI run, or new live experiment. Previously recorded 156-test and shared local
CI results remain historical records and were not rerun here.

## Adoption and recovery status

PR #6101 remains closed without merge. Its recorded PR head
`2ade22fa1d753cf509ac27c8567d935d8fbe82c2` differs from the observed source
tip, and its stacked base was deleted. PR #6114 merged into the old integration
branch, not into main. The referenced Issue #5256 is about optional
post-dispatch focused-target review context, not this stopped-caller API, so it
does not establish an aligned adoption contract. Do not reopen or merge the
stale PR as-is; any production successor needs a current-main review and a
directly aligned issue/contract.

The full source tip and history are also retained by remote tag
`archive/recovered/closed-6101-explicit-stopped-tip-f797619-20261003`. This
snapshot preserves discoverable source bytes while deliberately withholding
runtime adoption.
