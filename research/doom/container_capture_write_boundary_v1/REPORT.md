# Capture + PNG persistence/release boundary micro-test v1

Status: **WRITE_BOUNDARY_COST_CANDIDATE** in the rendered Xvfb/Tk/XTEST fixture.

This experiment removes exactly one component from the preceding full retained-artifact pipeline: PNG reopen/load. The remaining pre-release work is `ImageGrab -> PNG save -> fsync`.

## Frozen comparison

- `release_first`: KeyRelease+sync at the 250 ms deadline, then capture+PNG save+fsync.
- `pipeline_first`: capture+PNG save+fsync at the same deadline, then KeyRelease+sync.
- 12 balanced matched pairs; no retry.
- tens-of-ms candidate gate: median paired delta >= 10 ms OR p95 >= 20 ms.

## Result

| Metric | Release first | Write pipeline first |
|---|---:|---:|
| application-observed hold median | 249.906112 ms | 265.186984 ms |
| application-observed hold p95 | 250.088590 ms | 269.394892 ms |
| deadline -> KeyRelease median | 0.122901 ms | 15.614421 ms |
| pipeline total median | 15.630343 ms | 15.025321 ms |
| capture median | 3.131707 ms | 3.396434 ms |
| PNG write+fsync median | 11.993160 ms | 11.201271 ms |
| reopen/load | 0 | 0 |

Paired pipeline-first minus release-first application hold:

- median: **+15.846045 ms**
- p95: **+19.791359 ms**
- range: **+13.546381 to +20.542204 ms**

The median gate passes. PNG persistence before physical release is sufficient by itself to create a tens-of-ms-scale median hold extension in this simple fixture.

## Discovery ladder

Separate frozen runs, descriptive across runs:

1. capture present during hold: +0.101 ms median;
2. raw capture before release: +5.792 ms median;
3. capture + PNG save/fsync before release: +15.846 ms median;
4. capture + PNG save/fsync + reopen/load before release: +22.935 ms median.

The next test directly pairs step 3 against step 4, changing only reopen/load, so the reopen increment is measured without subtracting independent runs.

## Provenance

- base commit: `3c3dbe5ca3491694a544c0645018cf133a0c0ba9`
- source SHA-256: `efe20061ec1de8f7dffdbe2116569684dca3117bda27c8b264da598e58ac6797`
- preregistration SHA-256: `0c84520853f5105cb16a3e0218debf225ada3d46032ec059a94c68e105139e1f`
- result SHA-256: `cd2732b93925a70020ccae6f68ef8776abb7a906626b2e74f4a399e0a49ebea7`
- raw formal cases: 24

## Scope

Development mechanics only. No ViZDoom/gameplay efficacy, model, planner, human timing, hard-real-time or production-runtime claim.
