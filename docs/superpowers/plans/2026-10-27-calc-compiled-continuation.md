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
