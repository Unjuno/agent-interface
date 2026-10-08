# Whole-candidate scoring for compact intents — Issue #4877

Allocation: `qwen-sequence-ranking-4877-20260927-01`  
Base: `cd7853030248c0d19293bf573cd7c90109b1a57e`  
Branch: `research/qwen-sequence-ranking-4877-20260927`  
Path: `research/experiments/qwen_sequence_ranking_4877_v1/`

This is an inference-algorithm successor to #4861, not a rerun. It compares unconstrained generation, state-trie greedy decoding, and full-candidate conditional log-likelihood ranking on a fresh deterministic held-out seed. It performs no fitting and uses CPU-only Docker.

Only the local exact recovered #4792 adapter is eligible: model hash `c51dcfff55254b43559a8d02a831707fe309080d5fd958a44bef2d431f2f0f84`, config hash `c1b5c569cfaf10a4939e4f48ed59afb9c3dd5a78a655162b0354dfff7b57f4fa`. The divergent adapter in the old #4792 workspace and main is not used. Parent experiment code/artifacts remain unmodified.

No model loading or fresh row generation occurs until the source freeze and exact runtime/input gates are published. The local model cache (0.5B snapshot) and exact recovered adapter were verified in read-only mode. No GPU is allocated.
