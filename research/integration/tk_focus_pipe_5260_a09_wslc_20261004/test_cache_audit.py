import copy
import unittest
from cache_audit import cache_errors

class CacheAuditTests(unittest.TestCase):
    def setUp(self):
        self.row={'token':'fresh','app_start_ns':20,'app_end_ns':80,
          'app':{'xdg_cache_home':'/tmp/5260-a08-cache-abc_123'},
          'cache':{'token':'fresh','path':'/tmp/5260-a08-cache-abc_123','mode':0o700,'uid':65534,
                   'created_ns':10,'removed':True,'cleanup_started_ns':90,'cleanup_finished_ns':100}}

    def test_literal_owned_cache_binding_accepts(self):
        self.assertEqual(cache_errors(self.row),[])

    def test_wrong_parent_reuse_binding_bool_and_early_cleanup_refused(self):
        for mutate in (lambda r:r['cache'].update(path='/host/global'),
                       lambda r:r['app'].update(xdg_cache_home='/tmp/other'),
                       lambda r:r['cache'].update(uid=True),lambda r:r['cache'].update(removed=1),
                       lambda r:r['cache'].update(token='other'),
                       lambda r:r['cache'].update(cleanup_started_ns=50)):
            row=copy.deepcopy(self.row);mutate(row)
            self.assertTrue(cache_errors(row))

if __name__=='__main__':unittest.main()

