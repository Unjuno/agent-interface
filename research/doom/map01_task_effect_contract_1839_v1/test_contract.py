from __future__ import annotations
import copy
import unittest
from contract import classify
from oracle import oracle


def record():
    return {"session_id": "s1", "plan_id": "p1", "actuation_id": "a1",
            "clock_axis_attested": True,
            "physical": {"owner_id": "owner1", "empty_release_verified": True,
                         "down": {"session_id": "s1", "plan_id": "p1", "actuation_id": "a1",
                                  "owner_id": "owner1", "key": "space", "lower_ns": 100, "upper_ns": 110},
                         "up": {"session_id": "s1", "plan_id": "p1", "actuation_id": "a1",
                                "owner_id": "owner1", "key": "space", "lower_ns": 200, "upper_ns": 210}},
            "state_feedback": [], "task_effects": []}


class ContractTests(unittest.TestCase):
    def assert_agree(self, row):
        self.assertEqual(classify(row), oracle(row))
        out = classify(row)
        self.assertFalse(out["grants_input_authority"])
        self.assertFalse(out["grants_task_authority"])
        return out

    def test_positive_bound_effect_and_separate_state(self):
        x=record(); x["state_feedback"]=[{"session_id":"s1","observed_ns":150,"signal":"health","before":90,"after":80}]
        x["task_effects"]=[{"effect_id":"e1","session_id":"s1","plan_id":"p1","actuation_id":"a1",
            "observed_ns":220,"scorer_source":"independent_progress_clock_v2","scored":True,
            "scorer_independent":True,"controller_visible":False,"kind":"KILL_COUNT_INCREASE","polarity":"useful"}]
        y=self.assert_agree(x); self.assertEqual(y["task_effect"],"TASK_EFFECT_SCOPED")
        self.assertEqual(y["physical_actuation"],"PHYSICAL_ACTUATION_SCOPED")
        self.assertEqual(y["state_feedback"][0]["authority"],False)

    def test_state_only_is_not_task_effect(self):
        x=record(); x["state_feedback"]=[{"session_id":"s1","observed_ns":150,"signal":"ammo","before":5,"after":4}]
        y=self.assert_agree(x); self.assertEqual(y["task_effect"],"UNRESOLVED_NO_TASK_EFFECT")

    def test_effect_without_actuation_is_unbound(self):
        x=record(); x["physical"]={}; x["task_effects"]=[{"effect_id":"e1","session_id":"s1","plan_id":"p1","actuation_id":"a1",
            "observed_ns":220,"scorer_source":"independent_progress_clock_v2","scored":True,"scorer_independent":True,
            "controller_visible":False,"kind":"KILL_COUNT_INCREASE","polarity":"useful"}]
        self.assertEqual(self.assert_agree(x)["task_effect"],"UNRESOLVED_UNBOUND_OR_INVALID_EFFECT")

    def test_laundering_mutations_fail_closed(self):
        base=record(); base["task_effects"]=[{"effect_id":"e1","session_id":"s1","plan_id":"p1","actuation_id":"a1",
            "observed_ns":220,"scorer_source":"independent_progress_clock_v2","scored":True,"scorer_independent":True,
            "controller_visible":False,"kind":"KILL_COUNT_INCREASE","polarity":"useful"}]
        mutations=[]
        for path,value in [(('kind',),'VIEWPORT_PIXEL_CHANGE'),(('kind',),'HUD_HEALTH_CHANGE'),(('kind',),'PROGRAM_COMPLETED'),
                           (('plan_id',),'foreign'),(('actuation_id',),'foreign'),(('scorer_independent',),False),
                           (('controller_visible',),True),(('observed_ns',),109),(('scorer_source',),'controller')]:
            x=copy.deepcopy(base); x['task_effects'][0][path[0]]=value; mutations.append(x)
        x=copy.deepcopy(base); x['clock_axis_attested']=False; mutations.append(x)
        x=copy.deepcopy(base); x['physical']['up']['owner_id']='foreign'; mutations.append(x)
        x=copy.deepcopy(base); x['task_effects'].append(copy.deepcopy(x['task_effects'][0])); mutations.append(x)
        for x in mutations:
            with self.subTest(x=x):
                y=self.assert_agree(x); self.assertNotEqual(y['task_effect'],'TASK_EFFECT_SCOPED')

    def test_old_v38_v39_like_weak_records_refuse_effect(self):
        x=record(); x['physical']={}; x['state_feedback']=[]
        x['viewport_changed']=True; x['program_terminal']='completed'; x['run_final_score']={'kills':1}
        self.assertEqual(self.assert_agree(x)['task_effect'],'UNRESOLVED_NO_TASK_EFFECT')


if __name__ == '__main__': unittest.main()
