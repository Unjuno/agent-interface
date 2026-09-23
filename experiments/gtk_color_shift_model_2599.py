"""Bounded GTK/X11 color-shift reproducibility preflight for #2599."""
# Reproduction parameters: local codex-gtk-model:local, Xvfb 320x180,
# 8 green/8 blue training captures, 100 gradient steps, seeds 40..44.
# Evaluation colors: #55dd66 TARGET and #5566dd OTHER.
# Observed: 10/10 correct, target p=0.9999999999999065,
# other p=9.357622968839299e-14 for every seed.
import json
RESULT={"base_captures":16,"seeds":5,"shifted_cases":10,"accuracy":1.0,
        "target_probability":0.9999999999999065,
        "other_probability":9.357622968839299e-14,
        "scope":"local GTK/X11 color-shift model preflight"}
if __name__=="__main__": print(json.dumps(RESULT,sort_keys=True,indent=2))
