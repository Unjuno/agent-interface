# Two-phase observation publication micro-test v1

Status: **TWO_PHASE_OBSERVATION_PUBLISH_CANDIDATE** in the rendered Xvfb/Tk/XTEST fixture.

Both conditions capture the full frame before KeyRelease. The candidate changes only when durable publication runs.

- candidate: `capture -> KeyRelease+sync -> PNG save/fsync/reopen`
- baseline: `capture -> PNG save/fsync/reopen -> KeyRelease+sync`

This preserves the acquisition point while separating physical release from durable observation publication.

## Formal result

12 balanced matched pairs, first outcome only:

| Metric | Candidate | Baseline |
|---|---:|---:|
| application-observed hold median | 253.860300 ms | 274.571182 ms |
| app hold p95 | 256.233547 ms | 278.320391 ms |
| deadline -> KeyRelease median | 3.850587 ms | 24.548056 ms |
| capture median | 1.932860 ms | 2.102170 ms |
| publish total median | 19.807822 ms | 20.128506 ms |
| PNG write/fsync median | 11.329254 ms | 11.732394 ms |
| reopen median | 8.247121 ms | 8.093725 ms |
| raw/reopen pixel matches | 12/12 | 12/12 |
| app KeyRelease before publication end | 12/12 | 0/12 |

Paired baseline-minus-candidate application hold reduction:

- median **20.343747 ms**
- p95 **24.285405 ms**
- range **18.247852 to 26.147071 ms**

The preregistered candidate gate required >=10 ms median reduction, all raw capture pixel digests equal to their reopened artifact pixel digests, and all candidate application-observed KeyRelease timestamps before publication completion. All gates pass.

## Interpretation

The simple fixture supports a two-phase observation boundary analogous to the already-separated physical release/publication boundary: observation acquisition may need to occur before release, but durable image persistence and reopen need not hold input authority. Moving only publication after release preserves the captured pixel content and recovers about 20 ms median input occupancy without shortening or skipping publication itself.

The next gate is integration-only on the existing real MAP01/X11 fixture. Policy, owner deadline, scorer and model behavior should stay fixed; only capture/release/publication ordering should change.

## Provenance

- base commit: `5ea234d204e776774a6cdd46972cc0daa9b79766`
- source SHA-256: `37f7ca48bde64fcd791206d08e2b252f846716aa4b933f182b825160c374c049`
- preregistration SHA-256: `bc2ad5116e5abd40a5d899b6a46a7d55f82cf143bebddb3f500f084f7529bb3a`
- result SHA-256: `b37cbe2a23ce803bf1c044679c4c29f7642899e4a9b99c5a1ec6784e8b78e7fe`
- raw formal cases: 24

## Scope

Development mechanics only. No ViZDoom/gameplay efficacy, model, planner, human timing, hard-real-time or production-runtime claim.
