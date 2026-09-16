# Target footprint local repair through adaptive caller v3 — retained integration result

Status: **PASS_INTEGRATION_MECHANICS; no shared-runtime promotion.**

The experiment connects the previously retained outline-containing visual footprint resolver to the unmodified `adaptive_acquisition_caller_v3` local-repair boundary. The caller Git blob is `7faf042304728ce91a3e4f89d465b251ea0bf70d`; the resolver blob is `a8bb0e564bae738c9091b737ff2abe1922520ec1`.

## Result

One fresh Inkscape seed, seven scenarios, two arms, alternating order: 14/14 independently scored outcomes were condition-correct.

- `stable_static`: both arms complete without repair.
- `stable_pan`: baseline safely stops; candidate locally reacquires and completes.
- `moved_decoy`: baseline safely stops; candidate locally reacquires the moved circle rather than the same-color square and completes.
- `replaced_square`, `missing`, `duplicate`: both arms stop without task input.
- `post_repair_pan`: candidate first returns a no-authority local repair, then an external harness pan changes geometry before final revalidation. The unchanged caller's `final_revalidate` stops `association_changed`; task input is zero.

Across the block: wrong-target edits 0, model calls 0, release failures 0. Existing exact caller v3 regressions pass 12/12 and resolver regressions pass 8/8.

The candidate arm differs only by enabling one no-authority local repair on typed `association_changed`/`missing`. The shared caller source is unchanged and owns final revalidation, execution ordering and authority semantics. The result therefore supports adapter-level integration, not merging the resolver into a generic runtime default.

## Development failures retained

V1 was interrupted after three cases and exposed a contract error in the integration adapter: it attempted to return updated geometry from `reuse_revalidate`, but caller v3 intentionally preserves cached geometry on the revalidated-reuse branch. V2/V3 were incomplete due an Xvfb/Inkscape subprocess lifecycle issue in the multi-case wrapper. V4 changes only wrapper stdout/stderr handling and uses individually completed private desktops; scientific conditions remain the v3 contract.

## Scope and limitations

Single-seed integration mechanics only. Multi-seed resolver evidence exists separately in PR #335. Reference footprint and coarse target are fixture-authored. Pixel-identical semantic replacement remains an established observability boundary (PR #351), not solved here. Post-click selection races from Issue #327 are orthogonal. No model/game calls, no Chromium transfer, no MAP01 clear, no security-isolation or general speed claim.
