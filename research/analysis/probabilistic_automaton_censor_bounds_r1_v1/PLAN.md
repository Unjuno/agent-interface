# #1892 Censor-bound partial identification R1

H: with x=p*a, y=(1-p)*b and positive bounds a_L<=a<=a_U, b_L<=b<=b_U, the sharp p interval is [max(0,x/a_U,1-y/b_L), min(1,x/a_L,1-y/b_U)]. Exact censor points identify p; bounded censor information tightens the no-mechanism interval [x,1-y].
T: exact Fraction corpus over p=1/10..9/10, true a,b in quarters, every quarter-grid interval containing each true completion probability; candidate vs independent constraint intersection; A-only, completion-only and midpoint plug-in comparators.
D: interval mismatch0; true containment failures0; empty0; subset no-info; point-bound exact; strict tightening and partial intervals >0; both-bound strictly tighter than A-only >0/never wider; naive/midpoint wrong rows>0; formal1/reruns0.
C: deterministic censor-probability bounds are not statistical confidence intervals; estimating them is separate.
U: analytical partial-identification result only; no live estimate/prediction/authority/latency/product claim.
