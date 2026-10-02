"""Candidate gate with every supported nature-first public theta branch."""
import itertools
import json
import sys
from pathlib import Path

LIFETIMES=("FULL","ZERO","EVENT")
PHASES=("PRE_EVENT","POST_EVENT")
EVIDENCE=("VALID_0","VALID_1","MISSING","STALE")
ORDERS=("NATURE_FIRST_PUBLIC","AGENT_FIRST_REACTIVE")


def support(life,phase,evidence):
    if life=="FULL" and evidence.startswith("VALID_"): return [int(evidence[-1])]
    if life=="EVENT" and phase=="POST_EVENT" and evidence.startswith("VALID_"): return [int(evidence[-1])]
    return [0,1]


def action(theta): return "A" if theta==0 else "B"


def main(path):
    rows=[]
    for life,phase,evidence,order in itertools.product(LIFETIMES,PHASES,EVIDENCE,ORDERS):
        possible=support(life,phase,evidence)
        if order=="NATURE_FIRST_PUBLIC":
            # Exhaustively emit every publicly observed current theta in support.
            for theta in possible:
                rows.append({"lifetime":life,"phase":phase,"evidence":evidence,"order":order,
                    "support":possible,"observed_theta":theta,"decision":"CONTINUE",
                    "action":action(theta),"reachable_theta":[theta],"unsafe_dispatch":False})
        elif len(possible)==1:
            theta=possible[0]
            rows.append({"lifetime":life,"phase":phase,"evidence":evidence,"order":order,
                "support":possible,"observed_theta":None,"decision":"CONTINUE",
                "action":action(theta),"reachable_theta":[theta],"unsafe_dispatch":False})
        else:
            rows.append({"lifetime":life,"phase":phase,"evidence":evidence,"order":order,
                "support":possible,"observed_theta":None,"decision":"YIELD",
                "action":None,"reachable_theta":[],"unsafe_dispatch":False})
    controls=[{"lifetime":life,"order":order,"decision":"CONTINUE",
        "action":"SAFE_INDEPENDENT_OF_THETA","unsafe_dispatch":False}
        for life,order in itertools.product(LIFETIMES,ORDERS)]
    Path(path).write_text(json.dumps({"schema":"issue-6580-t0c-candidate-v1",
        "rows":rows,"negative_controls":controls},sort_keys=True,separators=(",",":")),encoding="utf-8")


if __name__=="__main__": main(sys.argv[1])
