# Issue #7387 T0 — synthetic serial-cue deck method gate

Status: frozen candidate/auditor package; no model or GUI inference. This finite construction checks whether matched synthetic image sequences and their hidden truth oracle are correctly bound before any model-facing assay is considered.

The Issue hypothesis is a lag-by-first-target-demand interaction in later-cue recognition. T0 does not test that hypothesis. It checks the prerequisites: fixed eight-frame sequences, lag and absolute-position crossing, balanced cue pairs, isolated cue controls, identical image bytes in `DUAL_REQUIRED` and `T2_ONLY`, no answer-bearing path/prompt metadata, complete denominators, and an independent pixel-level oracle.

Construction history: the first offline clean-fixture check failed because the auditor's triangle and cross masks extended one raster edge beyond the candidate's clipped drawing box. That construction failure was retained during development, corrected in the auditor, then rechecked. The final offline suite is 5/5; no formal candidate/auditor invocation occurred during construction.

## Frozen design

Four simple, computer-rendered glyphs (red square, blue disk, green triangle, purple cross); lags 1/2/4 frame slots; T2 absolute slots 4/5/6/7; all 12 ordered distinct cue pairs; eight frames per sequence. This yields 144 matched trials (288 presentations), plus 16 isolated controls. Frame-slot lag is not physical time. The fixture is authored, not human-validated; isolated-control distinctness is a pixel/oracle property only.

## Run

```powershell
wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M `
  --volume <package>:/src:ro --volume <fresh-output>:/out:rw `
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f `
  python -B /src/candidate.py --out /out

wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M `
  --volume <package>:/src:ro --volume <fresh-output>:/out:rw `
  python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f `
  python -B /src/auditor.py --out /out
```

Candidate and auditor are separate one-shot processes. Never rerun either formal invocation; preserve its first status. Construction tests are separate. WSLc memory flags are requests only: this host has reported missing cgroup/swap-limit capability.

## Scope

Even a clean T0 method PASS would establish only finite deck/oracle construction and mutation sensitivity. It would not establish model perception, a serial-interference effect, GUI observation latency, action correctness, safety, or runtime/product benefit. Any T1 needs fresh model-call ownership, a fixed model/version and prompt/schema, a powered design and independent scoring.

See [FREEZE.json](FREEZE.json) for the prospective source/image/main identities and [RUN.md](RUN.md) for the first formal outcome once one exists.
