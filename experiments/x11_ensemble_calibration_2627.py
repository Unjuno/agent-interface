"""Five-model aggregation preflight corresponding to Issue #2627."""
RESULT={"models":5,"green_probabilities":[0.3367468428,0.9999772676,0.8107119346,0.9850049572,0.6959877439],"green_average":0.7656857492,"blue_probabilities":[0.0032598103,0.0508881884,0.0201154160,0.5015559525,0.0125669356],"blue_average":0.1176772606,"average_threshold_green":True,"average_threshold_blue":False,"consensus_4_of_5_green":False,"consensus_4_of_5_blue":False,"scope":"direct X11 fresh-client ensemble preflight"}
if __name__=="__main__":
 import json; print(json.dumps(RESULT,sort_keys=True,indent=2))
