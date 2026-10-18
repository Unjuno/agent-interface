import copy
import json
import pathlib
import unittest

import auditor
import candidate

ROOT=pathlib.Path(__file__).parent
FROZEN=json.loads((ROOT/"protocol.json").read_text())
SMALL={**FROZEN,"ticks":36,"topologies":["ring"],"seeds":[11],"imitation_probabilities":[0.08]}
RAW=candidate.build(SMALL)

class AdoptionQueueTests(unittest.TestCase):
    def test_candidate_is_deterministic_and_raw_replay_matches(self):
        self.assertEqual(RAW,candidate.build(SMALL))
        result=auditor.audit(RAW,SMALL)
        self.assertEqual(result["errors"],[])
        self.assertEqual(result["groups"],len(SMALL["modes"]))

    def test_every_opportunity_and_obligation_is_accounted(self):
        for group in RAW["groups"]:
            events=group["events"]
            opportunities=[e for e in events if e["type"]=="opportunity"]
            self.assertEqual(len(opportunities),SMALL["ticks"]*SMALL["principals"])
            arrivals={e["id"] for e in events if e["type"]=="arrival"}
            completed={e["id"] for e in events if e["type"]=="completion"}
            unfinished={e["id"] for e in events if e["type"]=="unfinished"}
            self.assertEqual(arrivals,completed|unfinished)

    def test_auditor_rejects_five_frozen_mutations(self):
        mutations=[]
        target=RAW["groups"][2]["mode"]
        def group(x): return next(g for g in x["groups"] if g["mode"]==target)
        def drop_opportunity(x): group(x)["events"].pop(next(i for i,e in enumerate(group(x)["events"]) if e["type"]=="opportunity"))
        def alter_adoption(x):
            event=next(e for e in group(x)["events"] if e["type"]=="adoption" and e["principal"]!=0)
            event["after"]=not event["after"]
        def alter_service_order(x):
            event=next(e for e in group(x)["events"] if e["type"]=="service_start")
            event["tick"]+=1
        def alter_completion(x):
            event=next(e for e in group(x)["events"] if e["type"]=="completion")
            event["latency"]+=1
        def drop_unfinished(x): group(x)["events"].remove(next(e for e in group(x)["events"] if e["type"]=="unfinished"))
        mutations.extend((drop_opportunity,alter_adoption,alter_service_order,alter_completion,drop_unfinished))
        for mutate in mutations:
            altered=copy.deepcopy(RAW); mutate(altered)
            with self.subTest(line=mutate.__code__.co_firstlineno):
                self.assertTrue(auditor.audit(altered,SMALL)["errors"])

if __name__=="__main__": unittest.main()
