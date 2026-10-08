# Predicate-order audit hardening successor (#4994)

**Disposition: PASS_AUDIT_HARDENING_SCOPED.**

The fresh local-Docker successor preserves #4959's allocation-01 STOP and invalid host diagnostic unchanged. One new frozen allocation executed the unchanged 336-row retained corpus through the hardened auditor; 4/4 unit tests, the runner, and separate independent raw replay exited 0.

The mutation and malformed-input controls all rejected: three copied-raw mutations, three JSON non-finite constants, and six invalid weight values. Exact and rounded-valid weights passed their unit controls. The independent auditor reconstructed all 336 rows, 21 distributions, and crossover alpha 0.70 with zero errors. The original raw SHA-256 was unchanged before/after.

Detailed allocation logs, JSON result, and hash manifest: [allocation-01 results](results/allocation-01/).

Scope: one synthetic retained corpus and one local Docker image. This does not revise #4733's scientific conclusion or establish real timing, GUI/task effect, production authority, general JSON interoperability, or broad audit/security certification.