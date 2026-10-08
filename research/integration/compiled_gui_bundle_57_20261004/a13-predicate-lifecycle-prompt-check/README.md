# A13 predicate lifecycle prompt check

One model-only sample tests the explicit lifecycle wording against the exact retained synthetic #7422 R02 block-2/C/task-1 screenshot. The response satisfies the saved JSON schema and the A12 lifecycle wrapper: two action branches retain `target_valid=true`; neither action postcondition contains it; entry requires `exact_token_visible=true`; Submit and completion require `exact_saved_title=true`. Source points and the value crop are within the retained 1280×800 image.

The independent audit passes in normal and optimized Python. The corruption probe confirms both modes reject a forged transient action postcondition. Captured CLI JSONL, stderr, argv, answer, pinned inputs and audit are preserved here.

This is one sampled output. It does not establish visual-grounding correctness, actual GUI effects, robust prompt compliance, efficiency, or performance over a task set. It changes no #7422 result and uses no formal allocation.
