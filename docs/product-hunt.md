# Product Hunt positioning

## Name

Agent Interface

## Tagline

**A faster interface between AI agents and computers.**

## One-line description

Open research on a guarded local runtime that reduces redundant computer-use actions and observations without treating correctness as optional.

## Positioning

Do not launch this as “another GUI agent.” The product/research object is the systems boundary underneath a strong planner:

```text
planner -> semantic program -> local guarded execution -> meaningful observation only
```

The public repository is intentionally both the research record and the release artifact.

## What can be claimed today

- real X11 app harnesses exist for XTerm, Chromium, LibreOffice Calc, and Inkscape;
- route-level deoptimization and pre-execution guards have real-app evidence in the included experiments;
- raw reports and CSVs are public;
- the project is actively researching Observation Gating to suppress redundant model-visible screenshots.

## What should not be claimed yet

- production readiness;
- general cross-platform correctness;
- measured OpenAI/model token savings;
- end-to-end model latency gains;
- automatic general method discovery as a completed feature.

## Suggested launch media

1. Landing page hero showing the action/screenshot loop vs guarded local execution.
2. Short real-app recording with a stale route being guarded/deoptimized before failure.
3. One benchmark card with exact environment and `n` visible.
4. Repository/release link showing that the raw evidence ships with the release.
