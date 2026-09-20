# Measurement completeness note

The frozen runner records pretraining time and the four adapter update durations, but it does **not** isolate adapter construction/setup time. This is a preregistration measurement omission; no setup-time value is claimed and the formal allocation is not repeated. Each rank-2 output adapter has 16×2 + 2×4 = 40 trainable parameters (global control, B, and C each), directly from the frozen tensor shapes.

This omission does not alter the preregistered PASS gate, which is based on routed accuracy, invalid-route YIELD, base immutability, and exact snapshot/rollback state. It is a limitation for the requested efficiency characterization and must be measured in a separately preregistered successor if that comparison matters. All recorded update times and the scoped PASS remain as originally observed.
