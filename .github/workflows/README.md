# Workflow map

GitHub Actions in this directory serve different purposes. They are grouped here for navigation only; existing workflow files and triggers are unchanged.

## Public repository and release

- `pages.yml` — GitHub Pages publication.
- `research-preview-rc1.yml` — Research Preview release-candidate packaging/checks.
- `research-archive.yml` — retained research archive workflow.
- `capture-artifact-boundary-v1.yml` — artifact-boundary capture/checking.

## Runtime and portability

- `runtime-core-portability.yml` — promoted core portability checks.
- `runtime-kernel-v1.yml` — runtime kernel checks.
- `runtime-native-probe.yml` — native discovery/probe checks.
- `runtime-selector-v1.yml` — backend selector checks.
- `runtime-cli-v1.yml` — unified runtime CLI checks.
- `runtime-x11-v1.yml` — X11 backend checks.
- `runtime-win32-v1.yml` — Win32 backend checks.
- `runtime-quartz-v1.yml` — Quartz backend checks.
- `runtime-standalone-doctor.yml` — standalone doctor distribution checks.
- `runtime-portable-zipapp-v1.yml` — portable zipapp checks.
- `runtime-preview-artifact-v1.yml`, `runtime-preview-artifact-v2.yml` — runtime-preview artifact workflows.

## Repository maintenance

- `public-navigation.yml` — validates repository-relative links in the main public/navigation Markdown documents when those documents change.

- `analysis-index.yml` — checks that every retained `research/analysis/*/REPORT.md` result is linked from the analytical index and that index links do not point to missing directories.
- `research-workspace-index.yml` — checks that every top-level `research/` directory is reachable from `research/README.md` or `research/ROOT_NAMESPACE_MAP.md`.

## Research execution

- `container-lab-bundle-01.yml` — container research bundle execution.
- `map01-measurement-integration-live-02.yml` through `-04.yml` — scoped MAP01 measurement integration workflows.
- `map01-recovery-mechanics-dev-01.yml`, `-02.yml` — retained MAP01 recovery-mechanics development workflows.
- `map01-recovery-cover-mechanism-live-v3-01.yml` through `v6-01.yml` — versioned MAP01 recovery/cover live workflows.

The MAP01 workflows are retained as versioned research automation. Their existence does not mean all versions are current or promoted; read the corresponding retained reports and evidence.

## Maintenance rule

Do not infer project status from workflow filenames alone. New reusable automation should have a stable purpose; one-shot research automation should remain versioned and traceable to its evidence rather than silently replacing older workflow history.
