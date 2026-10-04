import copy
import json
import unittest
from adapter import mount_map, normalize_launch

F={'guest_source':'/inputs/source','guest_output':'/outputs/raw'}
M=[{'Type':'bind','Source':'/inputs/source','Destination':'/src','RW':False},
   {'Type':'bind','Source':'/outputs/raw','Destination':'/out','RW':True}]

class Mounts(unittest.TestCase):
    def test_both_permutations_same_closed_map(self):
        expected={'/src':('/inputs/source',False),'/out':('/outputs/raw',True)}
        for mounts in (M,list(reversed(M))): self.assertEqual(mount_map(mounts,F),expected)
    def test_seven_adversarial_mount_cases(self):
        cases=[]
        cases.append(M[:1]);cases.append(M+[{'Type':'bind','Source':'/other','Destination':'/extra','RW':False}])
        cases.append([M[0],M[0]])
        for key,value in [('Type','tmpfs'),('Source','/wrong'),('RW',True),('RW',0)]:
            changed=copy.deepcopy(M);changed[0][key]=value;cases.append(changed)
        for index,mounts in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(ValueError): mount_map(mounts,F)
    def test_normalization_is_derived_and_input_immutable(self):
        state={'State':{'ExitCode':0},'Mounts':list(reversed(M)),'Image':'sha256:literal'}
        receipt={'inspect_stdout':json.dumps(state),'command':['frozen'],'inspection':{'stdout':json.dumps(state)}}
        original=copy.deepcopy(receipt);result=normalize_launch(receipt,F)
        self.assertEqual(receipt,original)
        self.assertEqual(json.loads(result['inspect_stdout']),{**state,'Mounts':M})
        self.assertEqual(result['inspection'],original['inspection'])
    def test_duplicate_inspection_field_rejected(self):
        with self.assertRaises(ValueError): normalize_launch({'inspect_stdout':'{"Mounts":[],"Mounts":[]}'},F)

if __name__=='__main__': unittest.main()
