# A07 — KeyRelease-loss cleanup after ExecutorV13 schema correction

Question: when ExecutorV13 receives a valid `key_batch` step containing F8 DOWN then UP, does the selected V15 release path retry one injected dropped KeyRelease and reach server-neutral state before terminal publication?

A06 stopped before the first action because the synthetic step lacked required `op`; this run changes only that schema field and identifiers, using the same fake-X construction. This is one-shot; do not retry a candidate after invocation. No formal/live allocation, real X server, GUI, Doom, model, physical keyboard, or application effect.

Frozen base: `9febfe4926cde6629f9751d6444f6b802cf31328`; the 21-file source closure must match A06 pins byte-for-byte. Arms: normal KeyRelease and one dropped KeyRelease. Hypothesis-bearing treatment is only the injected loss arm.
