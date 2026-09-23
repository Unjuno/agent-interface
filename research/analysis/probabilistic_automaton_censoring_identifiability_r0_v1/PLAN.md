# #1890 Probabilistic automaton censoring identifiability R0

H: with next-state A probability p and state-dependent completion-before-censor probabilities a,b, observable completed rates are x=p*a and y=(1-p)*b. Completion-only normalization q=x/(x+y) equals p iff a=b; sign(q-p)=sign(a-b). Unknown a,b make p generally non-identifiable even when censor count is retained because x,y identify products only.
T: exact Fraction grid p=1/10..9/10, a,b in {1/4,1/2,3/4,1}; bias theorem, observable-equivalence groups, feasible interval x<=p<=1-y, state-independent control, naive comparators, independent audit.
D: theorem mismatch0; a=b q=p; a!=b nonzero correct-sign bias; ambiguous observable groups>0; interval violations0; naive wrong rows>0; censor-as-no-transition false rows>0; formal1/reruns0.
C: known/estimated censor mechanisms can restore identifiability; two-state minimal boundary only.
U: analytical probability-update prerequisite only; no real GUI estimate, prediction quality, authority, latency or product claim.
