import unittest
from candidate import planned_rows

class PlanTests(unittest.TestCase):
    def test_six_new_tasks_cover_recovery_refusal_and_baseline(self):
        fixture={'seed':52612026,'replicates_per_cell':2,'tasks':[
            {'id':'compact','payload':'hmt','geometry':'520x250+80+70'},
            {'id':'offset','payload':'hns','geometry':'580x270+140+100'}]}
        rows=planned_rows(fixture)
        self.assertEqual(len(rows),6)
        self.assertEqual({r['mode'] for r in rows},{'STABLE','DRIFT_REFUSE','DRIFT_RECOVER'})
        self.assertEqual(sorted((r['mode'],r['task_id'],r['payload'],r['geometry']) for r in rows),
            sorted((mode,task,text,geometry) for mode in ['STABLE','DRIFT_REFUSE','DRIFT_RECOVER']
                for task,text,geometry in [('compact','hmt','520x250+80+70'),
                    ('offset','hns','580x270+140+100')]))

if __name__=='__main__':unittest.main()
