# Pre-freeze construction repair

The first construction-suite invocation failed one assertion (1/4): the fixture's prose retrieval expectations were based on the old lexical-overlap design. Review of the A01 correction requirement showed that this design also varied retrieval-match rates between the memory representations, so merely changing the expected count would preserve a treatment confound.

Before any source freeze or formal candidate/auditor invocation, the design was corrected. Both memory arms now perform one exact relation-family lookup and retrieve the same record for each R candidate. The prose arm receives an untyped note; the structured arm receives typed boundary fields. The no-memory arm consumes one lookup slot against an empty memory. Common checks, candidate exposure, one review slot, and 64-word context remain equal. No formal candidate or auditor invocation occurred before this repair.

The initial failing assertion is retained here as construction history; the repaired suite must pass before freeze.
