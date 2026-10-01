# PNG reopen/load incremental pre-release cost v1

Status: **REOPEN_INCREMENT_CANDIDATE** in the rendered Xvfb/Tk/XTEST fixture.

Both conditions already execute `ImageGrab -> PNG save -> fsync` before KeyRelease. The only changed component is whether `Image.open/load/getpixel` also executes before release.

## Result

12 balanced matched pairs, first outcome only:

| Metric | Write only | With reopen |
|---|---:|---:|
| app hold median | 265.484383 ms | 271.119609 ms |
| app hold p95 | 272.665347 ms | 273.166274 ms |
| pipeline median | 15.175481 ms | 20.718009 ms |
| capture median | 3.258109 ms | 3.277336 ms |
| write/fsync median | 11.672727 ms | 11.202767 ms |
| reopen median | ~0 ms | 6.294386 ms |
| deadline -> release median | 15.660372 ms | 21.231575 ms |

Paired `with_reopen - write_only` app hold:

- median **+5.373113 ms**
- p95 **+8.683175 ms**
- range **-1.846571 to +8.994560 ms**

The preregistered increment gate was median >= 5 ms OR p95 >= 10 ms; the median gate passes. Reopen/load therefore contributes an additional ~5 ms median pre-release cost on top of capture+PNG persistence in this fixture.

## Consequence

The component decomposition now supports a more precise mechanism candidate: keep raw capture before release if needed for observation timing, but move durable publication work (`PNG save/fsync/reopen`) after physical release. The next micro-test directly compares `capture -> release -> publish` against `capture -> publish -> release` while preserving the captured frame source.

## Provenance

- experimental base commit: `85a73f4148d77a7204b36b3ae35b585bcbadabdd`
- publication branch base: `74e2d612d3344c3f35f71ab62c9ed29b426f58ac` after parallel MAP01 work advanced main
- source SHA-256: `c2deb84b4bf45d8aca84b2d914d9e97aae016a27155367fd5d713ac7e40cf95f`
- preregistration SHA-256: `8bc36d67b05386f070447f0a4800174c4e42dcc7eac6775a5b4b4cd9746d9a4c`
- result SHA-256: `509f4520c9334721bdf8bfc45c4237189a5306a5b418f40b97f86f6076c94701`
- raw formal cases: 24

## Scope

Development mechanics only. No ViZDoom/gameplay efficacy, model, planner, human timing, hard-real-time or production-runtime claim.
