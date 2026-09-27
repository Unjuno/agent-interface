# Scorer timing phase research (Issue #149)

Read REPORT.md before interpreting any timing. Stage 1 is HOLD under its full gates, despite the late schedule's lower median blocking. Stage 2 is a scoped one-shot rephasing candidate, not a production rollout.

## Exact source retention

`source.tar.xz.parts/000` through `002` are consecutive BINARY pieces, not encoded text. They contain 23 exact source/plan files, including both complete frozen plans, runners, acquisition/scheduling adapters and all tests. They are archived only to avoid duplicating a large versioned harness into many shared paths. No fonts or engine binaries are included.

```sh
cd research/doom/scorer_phase_schedule_v1
cat source.tar.xz.parts/000 source.tar.xz.parts/001 source.tar.xz.parts/002 > source.tar.xz
printf '%s  %s\n' 860cd53aff702187c2de856be2362acf80fb2801fdf8852e32c11eb2f9f5fb33 source.tar.xz | sha256sum -c -
tar -xf source.tar.xz
```

Source archive: 17188 bytes. Each uploaded Git blob was checked against the locally calculated identity; SOURCE_ARCHIVE.json lists part hashes. The two FREEZE files can be checked against the earlier commits; neither measured stage was retuned.

## Full retained replay

The complete conversation artifact `agent_interface_scorer_phase_research_20260916.zip` holds all raw controller/scorer records, 30 cases, 2 excluded preflights, images, integer timing ledger, source closure, and manifests. It is NOT uploaded to GitHub or Actions; archive.json pins its digest. Extract it into an empty directory, not the product runtime directory. No new GUI/game execution is required for replay.

From the extracted workspace:

```sh
python research/doom/scorer_phase_schedule_v1/replay.py . --pixels
python research/doom/scorer_phase_schedule_v1/audit_ledger.py research/doom/scorer_phase_schedule_v1/results/ledger.json
AI_RUNTIME_ROOT="$PWD/source-closure" PHASE_PREFLIGHT="$PWD/preflight-001" PHASE_PREFLIGHT2="$PWD/preflight2-001" python -m unittest discover -s research/doom/scorer_phase_schedule_v1 -v
```

Pixel replay needs Pillow; numeric replay uses the Python standard library. Tests use the retained preflights and source closure. Original measured environment: CPython 3.13.5, Pillow 12.3.0, ViZDoom 1.3.0; see environment.json. The data archive has no engine distribution. A new live study additionally needs the fixed runtime/wheel bundle (Actions artifact 10398313098), a newly frozen plan with new case IDs, and a private Xvfb/Openbox installation. Do not rerun consumed IDs or copy the archive over an existing checkout's product runtime.
