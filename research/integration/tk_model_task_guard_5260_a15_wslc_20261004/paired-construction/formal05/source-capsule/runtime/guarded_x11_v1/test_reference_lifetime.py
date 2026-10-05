"""Finite references and explicit fresh grounding with a controlled host clock."""
import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from PIL import Image
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from runtime.guarded_x11_v1.handles import TargetHandleStore

class ReferenceLifetimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.bridge=object.__new__(NativeHandleBridge)
        self.bridge.out=Path(self.tmp.name)
        self.bridge.session=SimpleNamespace(recovery_required=False)
        self.bridge.review_required=False;self.bridge.used_aliases=set()
        self.bridge.scope='lifetime:test';self.bridge.store=TargetHandleStore(self.bridge.scope)
        self.image=Image.new('RGB',(100,100),'white')
        for i in range(24):self.image.putpixel((38+i,44+i%12),(i*10,10,255-i))
        self.observation={'sequence':1,'capture_ns':1_000_000_000,'pointer_binding':{'focus':123,'surface':123,'geometry':[0,0,100,100]}}
        self.bridge.history={1:(self.observation,self.image)}
        self.assertTrue(callable(getattr(self.bridge,'mint_reference',None)), 'finite reference metadata API missing')

    def test_deadline_matches_actual_expiry_and_fresh_grounding_restores_resolution(self):
        with patch('runtime.guarded_x11_v1.bridge.time.monotonic_ns',return_value=1_000_000_000):
            minted=self.bridge.mint_reference('field',1,[50,50],region_size=(24,14))
        self.assertEqual(minted['offset'],[12,7])
        self.assertEqual(minted['lifetime']['minted_ns'],1_000_000_000)
        self.assertEqual(minted['lifetime']['expires_ns'],301_000_000_000)
        fresh={**self.observation,'sequence':2,'capture_ns':301_000_000_001}
        old=self.bridge.store.resolve_point('field',[12,7],fresh,self.image,301_000_000_001,self.bridge.scope)
        self.assertEqual(old['status'],'STALE');self.assertFalse(old['eligible'])
        self.bridge.history[2]=(fresh,self.image)
        with patch('runtime.guarded_x11_v1.bridge.time.monotonic_ns',return_value=301_000_000_001):
            renewed=self.bridge.mint_reference('field_fresh',2,[50,50],region_size=(24,14))
        valid=self.bridge.store.resolve_point('field_fresh',[12,7],fresh,self.image,301_000_000_002,self.bridge.scope)
        self.assertTrue(valid['eligible']);self.assertEqual(valid['point'],[50,50])
        self.assertEqual(renewed['lifetime']['expires_ns'],601_000_000_001)
        retained=json.loads((self.bridge.out/'mint-field.json').read_text())
        self.assertEqual(retained['expires_ns'],minted['lifetime']['expires_ns'])

    def test_deadline_is_not_pixel_or_capture_freshness_authority(self):
        with patch('runtime.guarded_x11_v1.bridge.time.monotonic_ns',return_value=1_000_000_000):
            row=self.bridge.mint_reference('field',1,[50,50],region_size=(24,14))
        self.assertFalse(row['lifetime']['authority_granted'])
        self.assertEqual(row['lifetime']['clock'],'time.monotonic_ns')
        self.assertEqual(row['lifetime']['capture_freshness_ms'],1500)
        stale=self.bridge.store.resolve_point('field',[12,7],self.observation,self.image,2_500_000_001,self.bridge.scope)
        self.assertEqual(stale['status'],'STALE')
        changed=self.image.copy();changed.paste('black',(38,43,62,57))
        mismatch=self.bridge.store.resolve_point('field',[12,7],self.observation,changed,1_000_000_001,self.bridge.scope)
        self.assertFalse(mismatch['eligible'])

    def test_legacy_mint_keeps_offset_contract(self):
        with patch('runtime.guarded_x11_v1.bridge.time.monotonic_ns',return_value=1_000_000_000):
            self.assertEqual(self.bridge.mint('legacy',1,[50,50],region_size=(24,14)),[12,7])

if __name__=='__main__':unittest.main()
