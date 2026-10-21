# PR audit disposition r02 — 2026-10-20

Live GitHub state was fetched on 2026-10-20 for PRs #8836 and #8841. Source
main was `5476ea072cd864bb603c3f801e492ce2163d34dc`; the bracketed complete
membership read is [r120](repository-inventory-recheck-20261020-r120.md).
This receipt supersedes only the r01 status rows for these two PRs.

| PR | Current live state | Exact head / recorded base | Evidence and disposition |
|---|---|---|---|
| [#8836](https://github.com/Unjuno/agent-interface/pull/8836) | Closed, unmerged, non-Draft | `afab8e406164e2e69de6ec25ba1724fa22f01d4e` / `f185a9059d485a4f8d5a65e9e7f6782897f67eae` | The published result is `FAIL_COST_GATE_SCOPED`; the saved audit missed a shared counter omission. Merged current-main successor [#9282](https://github.com/Unjuno/agent-interface/pull/9282), commit `302e8bc0681332329d3a2159668adc2f4dee906a`, preserves the result and frozen evidence; Issue #5311 remains open. Do not rerun the consumed allocation. |
| [#8841](https://github.com/Unjuno/agent-interface/pull/8841) | Open, Draft; `mergeable=true` at read | `04e7ddaa583fb3b120e9f3d00f3249c79c304f04` / `f185a9059d485a4f8d5a65e9e7f6782897f67eae` | Its unique 17-file construction packet was absent from current main. The four synthetic health/ammo/epoch test cases are separate from live-allocation A09 in #8749. Transfer the packet and canonical crosswalk first; preserve #59's live gates and keep #8841 open until the current-main copy and exact blobs are verified. |

## #8841 packet transfer verification

The original packet records frozen V39 source at `f185a9059d485a4f8d5a65e9e7f6782897f67eae`, four source-monitor cases, one WSLc test invocation, and a retained `PASS_SCOPED` non-executing audit. Its scope is construction only; it says nothing about a live model/game response, input release, recovery, task effect, or MAP01 completion.

On exact Git blob bytes at #8841's head, the original 16-entry package manifest had two stale entries: `results/audit.json` and `source_hashes.json`. The other 14 matched. The current transfer candidate corrects those two digests, adds this custody note and a package-local LF rule, and keeps the original audit/transcript/source/test blobs byte-identical. The saved audit checked source/test identity and the retained transcript, but not the package-wide manifest. All 18 current manifest entries now match staged Git objects.

Local CPython 3.11.9 `python -m unittest -v test_a09_pair_monitor` passed 4/4. A first Windows invocation of the saved non-executing audit against CRLF-converted working files produced a temporary mismatch and rewrote only the working copy of `results/audit.json`; that file was restored from the exact PR-head blob. An isolated copy extracted from staged Git blobs then returned `PASS_SCOPED`, with parsed JSON equal to the saved audit object. The initial mismatch was caused by the Windows checkout context and was not adopted as a scientific result. The package-local `.gitattributes` pins text to LF, and the transfer manifest is checked against staged Git blobs. No WSLc/Docker command, frozen formal command, or live allocation was rerun.

## State-change boundary

This receipt does not change any GitHub Issue or PR state. After a current-main
successor is merged, re-fetch #8841 and verify every transferred package blob
against its exact head. Only then close #8841 as superseded with a direct
successor link. Keep Issue #59 open until its separate live-control exit
conditions are evidenced. The #8836 custody loop is already complete through
#9282; select the next work from the remaining open PRs and current family map.
