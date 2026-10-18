# Post-run scope correction — A04

The frozen A01 and A03 decision records say “durable prefix counts.” That wording is too strong for the retained experiment. The candidate injected Python exceptions at ordinary file-operation boundaries and then observed the file contents. It did not simulate process termination or power loss, call `fsync`, or validate filesystem crash durability.

Read the result as an observed file prefix after an injected exception. The retry arm is synthetic and demonstrates duplicate rows in the later observed file contents; it does not claim that production automatically retries. The production executor behavior is separately described as source-reviewed, not runtime-integrated.

This is an additive post-run clarification. It does not change either frozen protocol, raw output, auditor, or result. No candidate or auditor was rerun.
