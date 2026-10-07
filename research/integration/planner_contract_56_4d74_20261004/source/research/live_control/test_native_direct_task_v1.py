import copy
import unittest
from native_direct_task_v1 import build_program
from runtime.core_v1.contract import validate_program

class DirectTaskTests(unittest.TestCase):
    def setUp(self):
        self.source={'sequence':7,'binding_revision':3,'native':{'width':1280,'height':800}}
        self.points={'source_sequence':7,'field_point':[329,401],'submit_point':[375,401]}
    def test_bound_batch_is_admitted_by_existing_contract_without_mutation(self):
        before=copy.deepcopy((self.source,self.points))
        program=build_program(self.source,self.points,'t991286-1','task-1',1000)
        validate_program(program)
        self.assertEqual(program['source'],{'observation_seq':7,'binding_revision':3})
        self.assertEqual(program['ops'][-1],{'op':'release_all'})
        self.assertEqual((self.source,self.points),before)
    def test_wrong_or_malformed_grounding_cannot_build_input(self):
        for changes in ({'source_sequence':6},{'source_sequence':True},
                        {'field_point':[float('nan'),1]},{'submit_point':[1280,10]},
                        {'field_point':[True,1]},{'field_point':[-1,1]},
                        {'submit_point':[20]},{'field_point':['20',1]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                build_program(self.source,dict(self.points,**changes),'token','task-1',1000)

if __name__=='__main__': unittest.main()
