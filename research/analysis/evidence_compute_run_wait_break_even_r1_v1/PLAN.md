# #1695 RUN/WAIT break-even under evidence invalidation risk

H: after #1687 hard feasibility, direct incremental expected costs are RUN=p*w and WAIT=(1-p)*g. For g+w>0, RUN iff p<g/(g+w), WAIT iff p>threshold, tie at equality. g=w=0 ties for all p. Hard CANCEL cannot be overridden.
T: exact Fraction grid, directed edge cases, hard-gate composition controls, naive-rule discriminator, independent audit, corruption controls.
D: threshold/direct mismatch0; hard-gate override0; naive mismatch>0; zero-zero ties all p; formal1/reruns0.
C: p/g/w require calibration and commensurate utility; no multijob/preemption/correlation model.
U: analytical one-horizon selector only; no empirical CPU/latency/model/product claim.
