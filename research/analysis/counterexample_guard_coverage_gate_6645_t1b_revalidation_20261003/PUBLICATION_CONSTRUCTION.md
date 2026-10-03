# Publication construction failure — not a research trial

Local source/evidence commit: 5dec3f2d3663513c184a8956c8884a0b0fb88971, parent/main at integration 1978f36e5d69c174c4a19ca0491664e856467407.

## First guarded push

Command: git --no-lazy-fetch push -u origin research/6645-t1b-integration-revalidation-20261003. Exit 1; no successful branch update was inferred.

Retained tool stderr:

```text
warning: lazy fetching disabled; some objects may not be available
fatal: could not fetch 91bf3ffd41e477327515057fe3ab73b5a8e1b59e from promisor remote
fatal: the remote end hung up unexpectedly
send-pack: unexpected disconnect while reading sideband packet
fatal: the remote end hung up unexpectedly
error: failed to push some refs to 'https://github.com/Unjuno/agent-interface.git'
```

Subsequent exact ls-remote showed the owned branch absent and main already at 3933b0c98b5ec39478d66ffe6829de6616839a1e. Remote is blob:none/promisor; push.negotiate is unset. The guarded HEAD-minus-origin/main object walk reports 58 objects, none missing, and the failed object is neither in that delta nor the current HEAD tree. Its cat-file lookup fails locally without lazy fetch.

## Bounded publication hypothesis

Default push relies on advertised refs for common commits. Main advanced after local fetch; the advertised tip is not locally known. Therefore publication may traverse historical objects instead of excluding the known parent. The installed Git 2.54 official config manual describes push.negotiate=true as using negotiation to find common commits, without needing a checkout/blob download.

Next scoped publication attempt enables only process-local push.negotiate=true and retains --no-lazy-fetch. No force push, source change, global config, physical/runtime experiment, historical blob hydration, or resource release. Its actual result is recorded in the PR/owning Issue after verification; this file does not predict success.

Publication retries are not scientific retries. Frozen host-audit count remains one, candidate/container zero; WSLc formal remains 0/0/0. Old record bytes and failed verifier evidence remain unchanged.

## Negotiation hypothesis outcome and exact-tree alternative

The process-local push.negotiate=true attempt at local commit 81f430d6f1037617ac6e31e1428a159029dd1ff2 also exited 1 with the same missing object/error sequence. Exact ls-remote again showed the owned branch absent. Negotiation alone did not resolve this failure; the historical-object packing cause is not proven. No lazy download was enabled.

The alternate publication path uses GitHub MCP Git-tree/commit/ref APIs, with base tree 40f1e4ad38784e8fe3d0b6f0106761b71b651771 and parent 1978f36e5d69c174c4a19ca0491664e856467407. It sends only the 54 changed UTF-8 files, then requires the server tree identity to equal the final local reviewed tree before creating the owned ref. This excludes historical blob hydration and preserves all base entries. The server commit identity may differ from the retained local commits; matching content-tree identity is the publication gate. The actual API outcome/tree/head are recorded on the owning Issue/PR, not predicted here. Main remains untouched until normal PR checks/review/merge gates pass.
