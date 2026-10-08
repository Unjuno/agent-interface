# Local `codex.exe exec` boundary (#2558)

This records the first local model-boundary smoke after the Docker/native path was repaired. It uses the host's installed Codex executable directly, with read-only sandboxing and a closed JSON schema. It is a boundary compatibility result, not a GUI task result or a replacement for the rich planner.

The model must return only `READY` or `YIELD`; the response grants no input authority. The next integration step is to use the same adapter for the existing compiled grounding schema and preserve the all-attempt ledger.
