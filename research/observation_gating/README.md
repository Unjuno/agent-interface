# Observation Gating

**Status: active research track.**

## First-principles question

If an observation contains no new task-relevant information, why should it cross the model boundary?

The goal is to reduce model-visible visual input without intentionally hiding state the agent still needs.

## Baseline ladder

```text
O0  full screenshot after each step
O1  exact unchanged-frame suppression
O2  exact changed-tile mask / spatial delta
O3  relevant-region gating
O4  local VERIFY before model escalation
O5  persistent visual state + ROI delta
O6  deterministic-route observation skip
```

## Hard gate

A candidate is not promoted if task correctness is lower than the paired baseline under the defined test.

## Primary metrics

- model-visible image observations eliminated;
- observed pixels / transmitted visual bytes;
- false-negative gating (relevant change suppressed);
- false-positive gating (irrelevant change escalated);
- action-to-first-useful-feedback latency;
- p50/p95/p99 local processing latency;
- escalation rate to full-frame observation.

Actual image tokens are a later model-in-loop metric. Pixel counts and bytes must not be renamed as tokens.

## Current safety choice

For the lossless first stage, exact frame/tile comparison is preferred over perceptual hashes. Perceptual similarity can miss small but semantically important GUI changes such as a character, cursor state, or compact control.

Approximate/perceptual methods can be tested only behind an uncertainty fallback and against adversarial small-change cases.
