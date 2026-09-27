# Construction record — Issue #3906

The adapter explicitly separates observation checks from compatibility normalization: every invalid-control identity is checked exactly, each finite feature is compared within `1e-6`, and NaN is accepted only as the exact serialized string at its declared position. A deep copy is normalized only after validation so the pinned #3899 auditor can perform the rest of its full-result checks. Raw input bytes are untouched and passed unchanged to that auditor.

Before freeze, run unit tests and `audit.py --self-test` inside cached local Docker with network disabled and source mounted read-only. These tests use synthetic unit fixtures only; they do not inspect the formal result or invoke model code.
