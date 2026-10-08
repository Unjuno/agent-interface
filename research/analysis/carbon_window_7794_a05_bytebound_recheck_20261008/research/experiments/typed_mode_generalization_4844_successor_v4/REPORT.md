# Issue #5184 — allocation -04 formal result

**Disposition: `HOLD_COVERAGE_TRADEOFF`.** The fresh-seed Docker Desktop runner and separate raw-only auditor each ran once and exited 0. The independent auditor reconstructed all 4,800 rows, reported `errors=[]`, rejected all 16 directed corruptions, and found zero unsafe emissions. None of the three preregistered primary blocks passed the full joint gate.

## H — hypothesis

For the disclosed synthetic five-mode/six-binary-cue family, typed mode-posterior aggregation through a fixed disposition map may reduce wrong emitted recovery versus direct disposition classification on partial/compositional holdouts, perhaps with inadequate benefit or excessive coverage loss. Direction was open.

## T — frozen execution

- Allocation `typed-mode-4844-successor-20260928-04`; training/heldout seeds 866309294/301332595; 2,000 balanced train rows and 4,800 heldout rows (960 per block, 192 per mode/block).
- Formal source freeze: commit `021fc64366cec2b0d3c16922c7c69760df7aae0c`; source commit `fe256c61c4557b5519c097a0ee86168c1b024512`. `FREEZE.json` binds exact source/test/plan blobs, hashes and sizes. Seed-pair searches immediately before launch found only the intended registration on #5184 and no other issue, PR, branch, commit or main-code match.
- Docker Desktop `desktop-linux`, Engine 28.5.1, pinned image config digest `sha256:1aaa65a85fda306ffb8b910824d4e93bdce61e212c7e87168123ea3073b41a1a` (`linux/amd64`). Both containers used no network, read-only root and source, 1 CPU, 512 MiB, 32 PIDs, `no-new-privileges`, and bounded `/tmp` tmpfs. Runner ID `b2694c8d1c42020718d774bdb18bf0380f0dec3c940e9e0239833d93dbeb7878`; auditor ID `aa6e675bc5ba0a8f773e9cb39cdb08d84f05e3e76e361bb1720ab82b1a58988c`; each exited 0 and was removed. No retries.
- Raw result: 1,541,863 bytes, SHA-256 `a2c9a758c45d6976f43cb239d44cbfaf0d67fdf4dc3b70118c938da0737e108a`. Raw rows, logs, IDs, full Docker inspect receipts and audit output are preserved under `formal/allocation-04/`.
- The separate auditor mounted only `result.json` read-only. Its receipt says `pass=true`, 4,800 rows, no errors, 16/16 corruption controls rejected, prototype and fail-closed controls passed, and zero unsafe emissions.

## D — frozen gates and result

The primary gate requires each of SINGLE_MISSING, MULTI_MISSING and COMPOSITION_HOLDOUT to reduce wrong emitted dispositions by at least 25%, without any wrong-recovery increase and with at most 5 pp safe-coverage loss. None meets all conditions.

| Block | Direct wrong | Typed wrong | Wrong reduction | Direct coverage | Typed coverage | Typed − direct coverage |
|---|---:|---:|---:|---:|---:|---:|
| SINGLE_MISSING | 70 | 59 | +15.71% | 39.688% | 72.500% | +32.813 pp |
| MULTI_MISSING | 56 | 72 | −28.57% | 42.604% | 70.521% | +27.917 pp |
| COMPOSITION_HOLDOUT | 209 | 137 | +34.45% | 71.563% | 63.333% | −8.229 pp |
| COMPLETE | 85 | 31 | +63.53% | 91.771% | 95.208% | +3.438 pp |
| NUISANCE_SHIFT | 129 | 117 | +9.30% | 66.771% | 67.396% | +0.625 pp |

SINGLE_MISSING improves wrong emissions by only 15.71%, below 25%. MULTI_MISSING emits 16 more wrong recoveries. COMPOSITION_HOLDOUT reduces wrong emissions by 34.45%, but coverage drops 8.229 pp, exceeding the frozen 5 pp allowance. Thus the preregistered conjunction fails; the auditor assigns `HOLD_COVERAGE_TRADEOFF`, not PASS. The prototype, unknown and contradictory controls pass in both arms; all unsafe counts are zero.

## C — controls and interpretation

The arms used identical generated train/test rows and information; only classifier factorization differed. Construction tests used seeds 59003/59004, passed 1/1 on each of two Docker Desktop invocations, and exercised deterministic output, balance, independent reconstruction and corruption controls. The formal seed pair is fresh relative to earlier registered pairs. This remains one finite authored family/seed pair, and classifier inductive biases differ. Do not pool it with allocation -03's two separately retained collision-related outputs.

## U — limits

This is synthetic classifier-family evidence only. It does not establish real GUI diagnosis, cross-app transfer, runtime integration/authority, safety, model quality, task effect, latency/token efficiency, human tempo or product readiness. Earlier #4844/#4863/#4155/#4169 and allocations -01/-02/-03 remain unchanged.
