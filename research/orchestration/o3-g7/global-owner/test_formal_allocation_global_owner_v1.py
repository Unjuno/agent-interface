import unittest
from formal_allocation_global_owner_v1 import select_global_owner
PATH='.github/workflows/live04.yml';ALLOC='live04'
def r(i,n,branch='main',sha=None,path=PATH):return {'id':i,'run_number':n,'path':path,'head_branch':branch,'head_sha':sha or str(i)*40,'status':'completed'}
def pick(rows,current,total=None):return select_global_owner({'workflow_runs':rows,'total_count':len(rows) if total is None else total},current_run_id=current,workflow_path=PATH,allocation_id=ALLOC)
class T(unittest.TestCase):
 def test_single(self):self.assertTrue(pick([r(1,1)],1)['may_enter_formal_step'])
 def test_different_sha_still_consumed(self):self.assertEqual(pick([r(1,1),r(2,2)],2)['result_class'],'FAIL_ALLOCATION_ALREADY_OWNED')
 def test_same_sha_consumed(self):self.assertFalse(pick([r(1,1,sha='a'*40),r(2,2,sha='a'*40)],2)['may_enter_formal_step'])
 def test_current_wrong_branch(self):self.assertEqual(pick([r(1,1,'dev')],1)['result_class'],'FAIL_CURRENT_WRONG_BRANCH')
 def test_wrong_branch_earliest_poison(self):self.assertEqual(pick([r(1,1,'dev'),r(2,2)],2)['result_class'],'FAIL_OWNER_WRONG_BRANCH')
 def test_other_path_ignored(self):self.assertTrue(pick([r(9,0,path='other.yml'),r(1,1)],1)['may_enter_formal_step'])
 def test_missing_current(self):self.assertEqual(pick([r(1,1)],2)['result_class'],'UNCERTAIN_CURRENT_RUN_NOT_VISIBLE')
 def test_malformed(self):self.assertEqual(pick([r(1,1),{'path':PATH,'head_branch':'main'}],1)['result_class'],'UNCERTAIN_MALFORMED_MATCHING_RUN')
 def test_truncated(self):self.assertEqual(pick([r(1,1)],1,total=2)['result_class'],'UNCERTAIN_TRUNCATED_API_VIEW')
 def test_duplicate_rows(self):self.assertTrue(pick([r(1,1),r(1,1)],1,total=2)['may_enter_formal_step'])
 def test_run_number_priority(self):self.assertEqual(pick([r(200,1),r(100,2)],100)['owner_run_id'],200)
 def test_cross_sha_reported(self):self.assertEqual(pick([r(1,1),r(2,2)],1)['cross_head_sha_count'],2)
if __name__=='__main__':unittest.main()
