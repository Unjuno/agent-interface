# P0 live causal effect diagnostic A3

BASE: `f035b30f4cd8a63fb3e690a31f5c6b30b1e6c3f9`
Issue: #1310
Science runner: exact parent blob `d8c509a55fe5363dc5211aebe510a720e964f7f3`.

Only changed factor: diagnostic persistence + failure-tolerant aggregation. Each child status is written before science-row read/aggregation; a supervisor row is written after Xvfb cleanup even for failed children; missing science fields cannot crash summary. Case child and science runner remain exact parent bytes. X11 remains unauthorized until a fresh #60 grant.

Construction: one matched pair / two fresh sessions. Any incomplete session => `PREFORMAL_SETUP_STOP_EFFECT_CHILD_DIAGNOSED`, scientific disposition NONE, stop. Only two complete unchanged-science rows authorize the already-frozen 6-pair formal block after ownership reread.
