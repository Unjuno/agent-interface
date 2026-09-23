# Issue #3873 OrbStack allocation successor

Issue #3864 seed 284935 completed three no-image schema preflights and stopped before any task. Its local runtime wrapper imported `event_socket_v11` from a hardcoded `/repo/research/live_control` path that did not match the canonical mount path. The three model calls and failure evidence remain unchanged in the v4 predecessor bundle.

This bundle reads the explicitly supplied `ISSUE3824_LIVE_SOURCE`, checks required runtime files before import, and adds an OrbStack-only startup/ready/clean-finish smoke. That startup gate performs no model or broker call. Formal allocation is fresh seed 284936, at most 17 calls, with retries disabled.
