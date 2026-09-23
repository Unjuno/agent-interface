# Compact-symbol presentation preflight (#2506)

This is an input-integrity gate for the matched model/provider allocation requested by #2506. It checks whether a compact symbol presentation preserves a bounded typed fact set. It does **not** call a model or provider, and therefore makes no claim about accuracy, token count, latency, or promotion value.

The audit is deliberately finite and adversarial: ordinary facts, ordering, unknown values, tampering, dictionary mismatch, extra fields, and evaluator-only fields. A passing result authorizes no external action; it only says that the representation/decoder pair is suitable for the next controlled allocation.
