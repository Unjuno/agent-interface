# Calc receipt-to-compiled-core integration Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans for the implementation, with regression tests before code.

**Goal:** Connect Calc stage evidence to the existing compiled-caller boundary without replaying uncertain input or treating program termination as task success.

**Architecture:** Implement a pure receipt-to-typed-facts mapper first, then compose it with the existing compiled core and caller in a test-only harness. Live socket observation/admission and independently scored effects are separate required deliverables, not simulated by the mapper.

**Tech Stack:** Python standard library; current `runtime/core_v1/compiled_gui.py`, `research/live_control/integrated_efficiency_compiled_execution_v2.py`, and Calc receipt v4.

**Spec:** `docs/superpowers/specs/2026-10-27-calc-compiled-continuation.md`.

## Global Constraints

- No live UI/input, WSLc, Docker, or historical allocation replay in offline construction. Do not modify preserved raw receipts.
- No coordinates or authority in symbols; no inference of input absence from zero completed steps.
- Keep independently verified task effects, input release, stale target, and uncertain delivery distinct.
- Required eventual comparison uses a fresh permitted allocation and same caller/accounting across arms.

## Review Focus

Malformed/missing receipt fields; multiple or conflicting terminals; focus-change interruption after possible input; historical-image freshness; absent or inconsistent release evidence; sink or verifier failures after partial work; target association changing between observation and input.

## Task 1: stage receipt mapper

Files: `research/live_control/calc_compiled_receipt_v1.py` and `research/live_control/test_calc_compiled_receipt_v1.py`. Define a closed typed result with explicit delivery uncertainty and verified empty release, preserving evidence identity and completed-step count. Use retained save/confirm receipt *copies or immutable bytes* to verify that `needs_decision` plus possible write produces stop/no-replay. Add negative tests for missing/contradictory terminals, malformed fields, unverified/nonempty release, and image references with no freshness claim. Run tests normally and with `python -O`.

## Task 2: composed offline seam

Files: `research/live_control/test_calc_compiled_caller_handoff_v1.py` and any narrowly necessary adapter. Compose the actual v3 caller and compiled core with inert Calc-shaped adapters. Verify a fresh revalidated target is required before input; an interruption after possible dispatch retains the receipt and stops without a blind second action; changed/unknown target does not receive input; outer effect verification remains independent. Retain all attempt accounting, including unavailable usage. Run this suite and existing caller/core handoff tests in normal and optimized modes.

## Task 3: live readiness and comparison

Specify actual observation-to-predicate evidence, target revalidation, bounded transport and terminal/release translation; implement and verify each before live use. Independently score persisted workbook contents and collateral effects. Freeze and run a separately permitted fresh three-arm cold/warm/invalidation/repair comparison only when the user-authorized environment and lane are available. Preserve all attempts, token/model metadata, time endpoints, raw evidence, failures, and scoped decision. Report missing accounting as unavailable.

## Task 1 implementation note (2026-10-27)

The pure mapper and four tests are added. Historical save/confirm receipts are read by their exact SHA-256 and produce stop, unknown delivery and no replay. Ruling: missing `keys_unknown` does not establish an empty release, even when older receipts say verified; this is conservative and can hold otherwise recoverable work. Historical image references are explicitly not fresh and retrievability is unverified. Task 2 and all live readiness work remain outstanding.

## Task 2 partial composition (2026-10-27)

A fail-closed terminal bridge and one composed interruption test now join the saved Calc receipt projection to the actual caller/core using an inert form-shaped graph. A returned stage receipt alone never supplies core completion or input authority; the test retains its projection in memory and proves one attempted action, no second action, uncertain delivery, no outer verification, and no completed core transition. This is not a Calc graph, durable receipt sink, live adapter, or a fresh observation. Existing 14 caller/core tests plus two bridge tests pass normally and under optimized Python. Changed/unknown Calc target composition and independent persisted-workbook scoring remain open.

## Task 2 receipt sink and stale-target check (2026-10-27)

A composed stage wrapper calls the supplied runner once, then sends a detached original receipt and projection to a supplied sink before returning a fail-closed core terminal. A stale admission prevents the stage call; a sink exception is propagated without retry and the caller returns CALLER_FAILED with uncertain delivery. The failure path has no returned core receipt and a failed sink does not prove durability; a stronger recovery/persistence design remains needed. Twenty synthetic caller/core/bridge tests pass normally and with `-O`. This is still an inert graph, not a Calc live adapter, fresh UI observation, or independent workbook score.
