# Inkscape conditional continuation over one public input owner

**Disposition: fixed-case correctness accepted; efficiency HOLD; no default change.**
The existing shared graph can conditionally continue through an application-authored public API adapter. A strong ordinary callback does the same. Both inspect a fresh post-release original image before Save, then stop before Save on an unknown cue. This qualifies this public-owner composition, not a transfer of `runtime.guarded_x11_v1.compiled` to Inkscape or general GUI perception.

## Frozen execution and actual primary use

Source `522b21e148170f9de12f27f3f0ffca44cbd2d938`, Inkscape1.2.2, separate empty400x240SVG, private1000x700Xvfb/Openbox, app window900x600 at20,20. Fixed order: positive ordinary, positive graph, unknown graph, unknown ordinary. `FROZEN.json` pins the plan/caller/predicate/schedule/test logs before first allocation. `source-modules.json` compares loaded-path files to the pinned Git source after execution; clean tracked state was checked before launch. This is not process/provider attestation.

Primary viewed the full original initial/final images for all four cases, explicitly chose the same two down-diagonal drags `(320,280)-(430,340)` and `(490,370)-(620,440)`, and closed each owner before allocating the next. Three commands per case: observe, method, close. No model resume between draw and Save; no subagent/background sensor. Twelve commands, six completed input programs, eight original primary images, fourteen total captures (ten inside methods). Both positive final PNGs have SHA256 `8229bbc24d92eadeea18cc744cc72633a0cb820845fb7807e1d0b2c8052af2ca`. Both positive SVGs are byte-identical, SHA256 `90d605571886c3e07464c808c3f89669987bd939217579baa761706fa0e22403`, independently parsed as two positive, in-page, nonoverlapping rectangles with no transforms. Independent persisted scoring is performed only after all owned processes are terminal.

Both negatives draw the same down-diagonal shapes but deliberately require the opposite up-diagonal cue. Both return `SAFE_YIELD/effect_unavailable`, one completed draw, zero Save. Final images show unsaved shapes; incidental pixels differ. Persisted SVG remains byte-identical to original emptySVG, SHA256 `1ed60353e3efda72ffa0509290ff9e3374745c5558db84360507493d687ad7b0`. These are deliberate task-contract mismatch controls, not spontaneous GUI changes, and are not successful save tasks. No repair/retry/extra observe/replay. All four original handles exited0; all owned PIDs were absent at terminal audit; Inkscape was terminated-15 by caller cleanup, Openbox/Xvfb exited0. Six dispatch and four close receipts verified neutral input.

## Equal execution policy and limits

Both routes use one `MCPSessionOwner.dispatch` and the same14-opdraw/4-opSave programs. The existing15/5-op reference programs' inline observations are replaced with explicit captures after dispatch returns and verified release; this is equal policy for these arms, not an optimized/default readiness policy. A fresh local capture precedes draw; source sequence advances2→3 for draw/Save. Two distinct caller leases receive the same2s expiry once before method publication, with no renewal. Method budget2s, at most2actions. Graph admission tokens are one-use; ordinary callback shares the admission/dispatch adapter. Public API focus/release/lease/source contract applies; this is not guarded alias/per-key revalidation. Bounded cooperative deadlines cannot preempt blocked I/O.

The fixed four-patch predicate reads hash-checked1000x700RGB only. It is retrospective trained on prior exact captures, narrow layout evidence, not a generic detector or independent persistence oracle. Clean title metadata is separately sampled after capture, not atomically associated withPNG and not proof of saved content. The core graph's `TASK_SUCCEEDED` is a local predicate verdict. Independent savedSVG and primary review remain separate requirements. No global WSL/Docker settings changed.

| Case | Local method ms | Helper publication→reply read ms | Publication→later primary review declaration ms | Inputs | Inside captures | Save |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| positive ordinary | 433.039 | 449.795 | 9313.728 | 2 | 3 | exact savedSVG |
| positive graph | 446.912 | 468.564 | 11259.257 | 2 | 3 | exact savedSVG |
| unknown graph | 295.419 | 325.782 | 11144.540 | 1 | 2 | none |
| unknown ordinary | 295.116 | 326.237 | 18807.054 | 1 | 2 | none |

Single observations with fixed200/300ms waits, evolving context/order/cache: no causal timing or economic advantage. Helper readiness/read is not delivery/ingestion by model. Primary declaration proxy includes orchestration/reasoning and is not pure inference, first useful feedback, or independently observed semantic completion. Human comparison and semantic-model latency are null. `report.json` also separates local draw-predicate knowledge. There are48 per-program physical emissions; native backend counters are cumulative across a connection and cannot be summed over dispatches. Positive draw10+Save4=14 each; negative draw10 each.

## Actual model accounting

Original chronological records expose one `gpt-6.1-sol/medium` context, without provider-build/identical-context attestation. Joint preparation inspection through terminal audit:2,202,087input,2,164,352cached subset,37,735uncached,10,957output (2,179reasoning subset),2,213,044total.61source records and8original image blocks independently reconstructed; exact reply-image multiset matches primary tool image inputs. Pricing/billing unavailable.

Method-tool-response-only uncached/output counts are1145/155ordinary positive,1373/139graph positive,1514/151graph unknown,1953/145ordinary unknown. These tiny windows exclude initial grounding, final review, startup/close and shared construction; they are not full task costs and do not measure costs caused by viewing the returned image. Joint includes them; never add across levels. Earlier preflight turn and first commentary before explicit begin, later accounting/publication, are excluded, not free. Shared construction and display correction are counted in joint. Evolving context/cache/fixed order prevents arm savings claims.

## Retained failures and checks

A preparation read used a nonexistent historical delivered_capture path before allocation; the actual existing integration-check module was used. First primary observe's largeJSON/base64 output was truncated, causing wrapper parsing failure. The command remained single-issued; caller read the same001reply and originalPNG instead of recapturing/replaying. Corrected later wrapper validates base64/image/artifact hashes before viewing. First audit incorrectly added cumulative emissions10+14; first outputs are retained and `audit-correction.json` records correction to program10+4 before publication. No input/source/primary decision changed.

Five meaningful adapter tests (paired input/source, unknown stop, release failure, expired authority, uncertain exception) pass normally/-O. Independent retained-case verifier passes normally/-O; seven positive/mutation tests reject changed caller, image/release/source/terminal/negativeSave. Actual usage reconstruction passes-O. Full runtime native397/192 was run on this exact production source earlier during the WSL recheck; its logs remain at `/var/tmp/agent-interface-wsl-migration-check-20261002-02` and are not relabeled as a new trial CI run. This evidence/guide update changes no production executable.

The next decision is whether graph structure supports requirements beyond a strong existing callback. This finite transfer does not justify replacing ordinary dispatch or promoting a performance default. Frozen first-domain comparison, summaryHOLD, and the broad live product goal remain open.
