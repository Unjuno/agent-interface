# A12 — planner predicate-lifecycle guard

## Question and frozen source

Can a small, versioned planner-schema guard reject the archived R02 contract that places transient `target_valid` in action postconditions, while accepting the A11-supported contract shape that keeps `target_valid` in branch conditions and fresh action admission and checks only the relevant resulting state? Does the guard still reject omission of the required saved-title effect?

This is a local schema-construction test over retained data. It does not call a model, run the graph, touch a GUI/input/provider, use a container, or consume an allocation. It changes no historical contract, score, or raw record.

Frozen source tree: `9fa379bb080f520f8f7d8080646857ca144243e7`. Pinned task JSON SHA-256 `80535efedb1af9bfa1b16346d66f27b10bf1119c21038629b08e3cb79356fc64`; baseline planner schema `c6b6ee14f9504c658e51128d35c150a830981c33773093ec01d4b83190271936`; prompting runner `2aba0139f6e1158b4f64d04b9c7d78ca7234b90412f2881165e6464c609edbc1`; compiled runtime `d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014`.

## H/T/D/C/U

- **H:** The baseline compiler accepts the R02 authored contract despite its post-action `target_valid` requirement. A versioned guard that reserves this transient predicate for branch conditions rejects that contract; removing only `target_valid` from authored action effects yields a compilable graph while preserving pre-action guards and `exact_saved_title` completion.
- **T:** Read the pinned task contract; run baseline schema and proposed wrapper on (1) original contract, (2) contract with only `target_valid` removed from each action expected effect, and (3) corrected contract with required `exact_saved_title` removed. Inspect compiled branch/effect fields.
- **D:** Baseline accepts (1); wrapper rejects (1) with the specific lifecycle error, accepts (2) with `target_valid` retained in both action branches, and rejects (3) through the existing required-effect guard. Any deviation is FAIL.
- **C:** This is one task-specific predicate vocabulary and a local wrapper proposal. It may not generalize to other observer predicates, apps, or model-authored contracts.
- **U:** The model was not called, so adoption compliance is unknown. No measured task effect, transfer, end-to-end efficiency, or confidence interval is available.

No success threshold may be changed after execution. Record the first successful run and preserve all inputs and hashes.
