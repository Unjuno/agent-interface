# Real kernel lifecycle adapter successor #2333

Status: PASS_KERNEL_LIFECYCLE_ADAPTER_SCOPED

This research-only fixture executes the existing platform-neutral
runtime/kernel RequestLifecycle through a deterministic synthetic adapter.

It verifies one positive path (observation → binding → authority → execution →
verified effect), stale binding rejection, expired lease rejection, non-empty
release rejection, verified cleanup stop, and an unknown boundary refusal.

Native and python:3.12-slim container audits passed in GitHub Actions run
35446190109, including source-blob, syntax, and JSON checks.

The fixture does not modify runtime/kernel or runtime/cli_v1 and makes no GUI,
model, OS input, network, latency, token, human-tempo, or production claim.

Reproduction:

    python audit.py
