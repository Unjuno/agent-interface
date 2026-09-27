# Retained-artifact/release boundary micro-test v1

Status: **RETAINED_ARTIFACT_BOUNDARY_COST_CANDIDATE** in the rendered Xvfb/Tk/XTEST fixture.

This is the next one-variable discovery step after the raw capture/release ordering test. The 250 ms hold, key, fixture, XTEST path and release ordering comparison stay fixed. The only added complexity is retained-observation artifact work after capture:

`ImageGrab -> PNG save -> fsync -> Image.open/load/getpixel`.

## Frozen conditions

- `release_first`: send `KeyRelease` + X sync at the 250 ms deadline, then execute the identical retained-artifact pipeline.
- `pipeline_first`: execute the retained-artifact pipeline at the deadline, then send `KeyRelease` + X sync.
- 12 balanced matched pairs; no retry.
- primary metric: paired `pipeline_first - release_first` application-observed press-to-release duration.
- tens-of-ms candidate gate: median >= 10 ms OR p95 >= 20 ms.

## Result

| Metric | Release first | Pipeline first |
|---|---:|---:|
| n | 12 | 12 |
| application-observed hold median | 250.082511 ms | 272.988332 ms |
| application-observed hold p95 | 250.941470 ms | 303.501360 ms |
| deadline -> KeyRelease median | 0.126134 ms | 23.253667 ms |
| pipeline total median | 22.228851 ms | 22.597774 ms |
| capture median | 2.959994 ms | 2.950288 ms |
| PNG write+fsync median | 11.955725 ms | 12.952450 ms |
| reopen/load median | 7.207731 ms | 6.586087 ms |
| KeyRelease send -> app release median | 0.616652 ms | 0.536613 ms |

Paired `pipeline_first - release_first` application hold:

- median: **+22.934795 ms**
- p95: **+52.448903 ms**
- range: **+20.573388 to +79.955457 ms**

The preregistered tens-of-ms gate passes strongly. The added occupancy closely follows retained-artifact pipeline duration.

## Interpretation

The prior raw-capture boundary test added about 5.8 ms median. Adding PNG encode/write/fsync and reopen/load increases the pre-release cost into a tens-of-ms regime. In this simple rendered fixture, completing retained observation work before physical input release is therefore a concrete mechanism capable of producing the scale of retention previously seen in more complex capture-coupled paths.

This is not yet a runtime integration recommendation. The next attribution step removes only reopen/load while keeping capture + PNG write + fsync, so persistence and reopen costs are separated before any shared-runtime change.

## Provenance

- base commit: `93411eb11aff6bfd2244bd8ecaae89e017ed5b99`
- source SHA-256: `be23884611248a2340864bed14af6647013956be85fd86c4d99a7f85950b43fc`
- preregistration SHA-256: `22f7afc1865db7c0fea462d303215ce80118f660ec02038a996f1c5c768acba3`
- result SHA-256: `931e1d191cb02dcdd4d8ffbd440b7adee78d8fde2111f4bd7022fa41b9690e53`
- raw formal case count: 24
- construction smoke: 2 pairs, excluded from formal aggregation

## Scope

Development mechanics only. No ViZDoom/gameplay efficacy, human timing, hard-real-time, model, planner, or production-runtime claim.
