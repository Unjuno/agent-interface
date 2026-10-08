# Recovery status — Issue #3850

This package preserves two pre-result STOPs; neither is a model-quality result.

- Allocation 01 was not consumed. No formal model calls or Docker formal rows
  started. Preflight found a duplicated `Task:` prompt protocol and an
  unowned/transient Docker resource state. The prompt was not sent to a model.
- The one-row successor recorded one CLI request but zero completed model
  turns; seven rows were unattempted. The supported CLI/auth path could not be
  shown to isolate configured MCP servers without inspecting or mutating
  private user configuration. No further prompt was sent.

Construction/schema checks and their pre-formal failures remain as historical
records. No model call, formal allocation, CLI probe, or Docker experiment was
run during this archival recovery. Any future attempt requires a separately
reviewed allocation with strict output-schema, single-owner result-directory,
and auth-safe tool-isolation preflight.
