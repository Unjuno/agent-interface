# Product Hunt positioning

> **Document role:** presentation/launch-positioning notes. This page is not the canonical source for current research status or release readiness; use [`PROGRESS_FROM_BASELINE.md`](PROGRESS_FROM_BASELINE.md), [`EVIDENCE_MAP.md`](EVIDENCE_MAP.md), and [`../release/README.md`](../release/README.md).

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

The public repository is the research record. Runnable user distributions have
a separate release gate; see [release contract](../release/README.md).

## What can be claimed today

- real X11 app harnesses exist for XTerm, Chromium, LibreOffice Calc, and Inkscape;
- route-level deoptimization and pre-execution guards have real-app evidence in the included experiments;
- raw reports and CSVs are public;
- the project is actively researching Observation Gating to suppress redundant model-visible screenshots.
- scoped O1/A2 experiments and actual assistant-operated sessions are recorded;
  use the [research handoff](LOCAL_RESEARCH_HANDOFF.md) for exact claims and limits.

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
5. Later: real-time DOOM with the assistant choosing actions while the game keeps
   running at normal speed. Link a short edit to an uninterrupted master and
   synchronized input/observation traces; disclose the model and local controller
   roles. This demo has not been built or recorded yet.
