#!/usr/bin/env python3
"""Pre-formal source and oracle construction checks; does not invoke the learner."""
import copy

def run(ns):
    alpha=ns["ALPHABET"]; target=ns["TARGET"]; oracle=ns["Oracle"]()
    assert len(alpha)==6 and set(target)=={"V","T","H","P","A","X"}
    assert all(set(row)==set(alpha) for row in target.values())
    assert len({oracle.state(prefix) for prefix in ns["ACCESS"].values()})==4
    assert [oracle.member(w) for w in ns["BASELINE_CASES"]]==[True,False,False,True]
    # The baseline policy mutant is accepted on each frozen example but admits EBP.
    mutant=copy.deepcopy(target); mutant["T"]["B"]="P"
    assert all(ns["_accept"](target,w)==ns["_accept"](mutant,w) for w in ns["BASELINE_CASES"])
    assert ns["shortest_false_accept"](target,mutant)=="EBP"
    cert={"trans":target,"accept":{"A":True,"V":False,"T":False,"H":False,"P":False,"X":False},"start":"V"}
    assert ns["equivalence"](target,cert,"V")["equivalent"] is True
    bad=copy.deepcopy(cert); bad["trans"]=copy.deepcopy(target); bad["trans"]["T"]["B"]="P"
    got=ns["equivalence"](target,bad,"V")
    assert got["equivalent"] is False and got["counterexample"]=="EBP"
    return "PASS_CONSTRUCTION 7 checks"
