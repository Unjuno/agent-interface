C08 — MAP01 v39 release-publication ordering candidate
Date: 2026-10-04

C07 froze ExecutorV12 and a deterministic barrier test. The test failed because terminal was emitted while the cancellation-release publisher was gated. C08 retains the existing ExecutorV13 implementation (which has a submit-time watcher and synchronous pre-terminal publication), adds a direct gated-publication regression test, and introduces session_map01_v15 to select ExecutorV13 in the MAP01 composition.

Scope is fake backend / in-process tests only. No game, X server, live input allocation, or live MAP01 run was used. This evidence proves event ordering for the exercised executor path and wrapper selection; it does not prove game task-effect, performance, live recovery, or resource bounds.

Tests: order barrier 1/1; ExecutorV13 2/2; ExecutorV12 2/2; v12-owner integrated cancel cause 1/1; transition owner v4 1/1; release backend v3 composition and actual composition; session v15 selection 1/1. See per-test raw stdout and exit files. All locally run tests passed.
