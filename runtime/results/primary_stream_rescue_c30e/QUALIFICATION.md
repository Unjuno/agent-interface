# Current-main primary stream rescue checkpoint

Source: closed, unmerged PR #6979; c30e354acd6ca267ace6e3f0ba6c28612091aade.
Current baseline: 254797822566aa2c64ca0d8a59ccca83722fbe53.

482 immutable original files restored in four current_primary integration packets;
478 manifest/SHA256SUMS targets matched. Cached source-relative diff was empty.
V1 uses SHA256SUMS, not MANIFEST.json; the first schema probe failed with
FileNotFoundError before the corrected checker. Original evidence was unchanged.

Fresh ordinary macOS Node v26.7.0 qualification (not formal allocation replay):
- Original unchanged direct close tests: main RED 5 tests, 3 failures;
  emit-only GREEN 5/5.
- Existing main stdio and fatal UTF-8 tests: 27/27.
- Original unchanged real inert relay owner-close tests: 2/2.
- Original seven appended owner/startup tests plus existing failure-order tests:
  emit-only RED 21 tests, 5 failures (unhandled readline, ready/terminal errors).
- Composed owner-first-failure/close repair with fatal UTF-8 preserved:
  43/43, zero skips/cancellations. Raw first RED and later GREEN logs remain
  separately saved in the task outputs directory; they are not rewritten.

The implementation selectively composes old owner fault observation and silent
Writable close settlement. Whole-file source replacement would remove current
fatal UTF-8 admission and was explicitly rejected.

STOP / pending: local CI43 not yet qualified on this checkpoint; advisory review
pending; Node22 hosted and Windows/native applicability are not established.
Docker's Python image has the previously observed containerd blob access failure;
no daemon reset/prune/shared-container reuse was performed. Native effects,
delivery, GUI/backend authority, and original scientific results are not inferred
from injected Writable or inert relay tests. Original proposal committee quorum,
current-tree applicability and sole-sender requirements do not transfer to this
composition. No main merge, original ref retirement, or parent Issue closure.
