# Pre-freeze construction defect

The draft candidate aliased the input epoch list and mutated its own initial-state record during transitions. Independent audit rejected state 0 (`FAIL_METHOD`, `state_inventory:0`). This was not a frozen allocation, and no scientific inference is made. Raw SHA-256: candidate `48197ef3252b71d04dc87eec879b5fb5c324a5e8c8ca90809c5e77f7241f28b5`; audit `647891b4eda4a5dbb1feaa3ce05ba1f1477b018c6108072e5f0b4ff8d8eeb629`.
