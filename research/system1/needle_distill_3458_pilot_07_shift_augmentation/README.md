# Needle pilot-07: targeted near-boundary training augmentation

Issue #3918 tests one narrow intervention after pilot-06: replace half the training CORRECT examples with in-envelope near-boundary examples, keeping the small model, fixed update count, paired initialization, minibatch stream, hybrid gates and evaluation contract fixed. The control and treatment use three fresh paired seeds.

See [PREREGISTRATION.md](PREREGISTRATION.md) for H/T/D/C/U and [FREEZE.json](FREEZE.json) for pinned source, data mappings, cached Docker image and the one-shot command. The independent auditor does not import the runner. Construction tests do no model training.
