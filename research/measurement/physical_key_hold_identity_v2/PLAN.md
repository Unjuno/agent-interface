# Physical key hold actuation identity v2
TASK: PHYSICAL-KEY-HOLD-ACTUATION-IDENTITY-20260917-002
BASE: e690e155aa00fb72a30586513caf9bfeec9a8a7d
ISSUE: #1023
H: one confirmed physical hold gets exactly one owner-local actuation generation; repeated down reuses it, confirmed matched up/cleanup retires it, and later independent hold advances generation.
T: source-first pure Python candidate + structurally distinct history oracle; fixed controls; seed99920260917002; 250000 independent lifetimes length1..20 in25 immutable chunks of10000; no chunk reruns; aggregate+audit after all chunks.
D: PASS only if candidate/oracle agree every step; false mint/reuse/cross-lineage retirement/multi-ID hold all0; fixed controls pass; 25/25 chunks complete once; integrity passes.
C: synthetic edge-confirmation input only; no X11 truth or authority.
U: construction-only predecessor for #998.
