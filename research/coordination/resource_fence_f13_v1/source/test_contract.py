import json
from pathlib import Path
import tempfile
import unittest
from experiment import Peer

class Contract(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.record={'peers':[],'io':[]}
        self.peer=Peer('resource','INSTALLED_EPOCH',Path(self.temp.name),'unit',0,self.record)
    def tearDown(self):
        self.peer.finish()
        self.temp.cleanup()
    def apply(self,epoch=7,rid='A',scope='unit',value=1):
        return self.peer.send({'op':'apply','grant':{'scope':scope,'epoch':epoch,'id':rid,'value':value}})['status']
    def test_stable(self): self.assertEqual(self.apply(),'APPLIED')
    def test_duplicate(self):
        self.apply();self.assertEqual(self.apply(),'DUPLICATE')
    def test_conflict(self):
        self.apply();self.assertEqual(self.apply(value=2),'CONFLICT')
    def test_scope(self): self.assertEqual(self.apply(scope='other'),'BAD_SCOPE_OR_TYPE')
    def test_boolean(self): self.assertEqual(self.apply(epoch=True),'BAD_SCOPE_OR_TYPE')
    def test_uninstalled(self): self.assertEqual(self.apply(epoch=8),'WRONG_EPOCH')
    def test_installed(self):
        self.peer.send({'op':'install','expected':7,'next':8})
        self.assertEqual(self.apply(),'WRONG_EPOCH')
        self.assertEqual(self.apply(epoch=8,rid='B'),'APPLIED')
    def test_rollback(self):
        a=self.peer.send({'op':'install','expected':7,'next':6})
        self.assertEqual(a['status'],'WRONG_EPOCH')
        self.assertEqual(self.apply(),'APPLIED')

if __name__=='__main__': unittest.main(verbosity=2)
