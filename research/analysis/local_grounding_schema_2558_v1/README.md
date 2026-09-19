# Local compiled grounding schema boundary (#2558)

This is a successor evidence artifact for the unresolved model-boundary part of
Issue #2558. The host-local `codex.exe exec` adapter consumed the retained
Docker-native observation image and returned a `compiled-form-grounding-v1`
object. The JSON Schema validator accepted it.

This experiment deliberately stops before input emission. Coordinates and
method are model output, not authority. The next gate must independently
revalidate focus, target geometry, field pixels, and the post-action effect;
otherwise the result is `YIELD`.
