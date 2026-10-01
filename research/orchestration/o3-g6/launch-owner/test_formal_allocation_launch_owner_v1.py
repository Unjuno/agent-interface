import unittest
from formal_allocation_launch_owner_v1 import select_owner

PATH='.github/workflows/formal.yml'
SHA='a'*40
ALLOC='formal-01'

def run(i,n,status='in_progress',path=PATH,sha=SHA):
    return {'id':i,'run_number':n,'path':path,'head_sha':sha,'status':status}

class TestOwner(unittest.TestCase):
    def pick(self, rows, current):
        return select_owner({'workflow_runs':rows},current_run_id=current,workflow_path=PATH,head_sha=SHA,allocation_id=ALLOC)
    def test_single_run_owns(self):
        self.assertTrue(self.pick([run(10,1)],10)['may_enter_formal_step'])
    def test_earlier_run_owns_concurrent_pair(self):
        out=self.pick([run(10,1),run(11,2)],10); self.assertEqual(out['result_class'],'PASS_CANONICAL_OWNER'); self.assertEqual(out['owner_run_id'],10)
    def test_later_run_fails_concurrent_pair(self):
        out=self.pick([run(10,1),run(11,2)],11); self.assertEqual(out['result_class'],'FAIL_NOT_CANONICAL_OWNER'); self.assertFalse(out['may_enter_formal_step'])
    def test_completed_prior_owner_still_blocks_second_run(self):
        out=self.pick([run(10,1,'completed'),run(11,2,'in_progress')],11); self.assertTrue(out['prior_completed_owner']); self.assertFalse(out['may_enter_formal_step'])
    def test_duplicate_api_rows_deduplicate_by_id(self):
        out=self.pick([run(10,1),run(10,1)],10); self.assertEqual(out['matching_run_count'],1); self.assertTrue(out['may_enter_formal_step'])
    def test_other_sha_ignored(self):
        self.assertTrue(self.pick([run(10,1),run(9,0,sha='b'*40)],10)['may_enter_formal_step'])
    def test_other_workflow_ignored(self):
        self.assertTrue(self.pick([run(10,1),run(9,0,path='other.yml')],10)['may_enter_formal_step'])
    def test_current_run_not_visible_fails_closed(self):
        out=self.pick([run(10,1)],11); self.assertEqual(out['result_class'],'UNCERTAIN_CURRENT_RUN_NOT_VISIBLE'); self.assertFalse(out['may_enter_formal_step'])
    def test_malformed_matching_run_fails_closed(self):
        out=self.pick([run(10,1),{'path':PATH,'head_sha':SHA,'run_number':0}],10); self.assertEqual(out['result_class'],'UNCERTAIN_MALFORMED_MATCHING_RUN'); self.assertFalse(out['may_enter_formal_step'])
    def test_run_number_beats_id_for_owner(self):
        out=self.pick([run(200,1),run(100,2)],100); self.assertEqual(out['owner_run_id'],200); self.assertFalse(out['may_enter_formal_step'])

if __name__=='__main__': unittest.main()
