"""Excluded pure-byte construction tests; no formal/session reuse."""
import base64
import copy
import hashlib
import json
import unittest
from study import policy, components

def picture(boxes, width=320, height=120):
    b=bytearray(width*height*4)
    for x,y in boxes:
        for j in range(y,y+16):
            for i in range(x,x+16): b[4*(j*width+i)+1]=255
    return {'w':width,'h':height,'depth':24,'b64':base64.b64encode(b).decode()}

class Contract(unittest.TestCase):
    def setUp(self):
        self.binding={'session':'unit','window':123,'generation':1,'domain':[0,0,320,120]}
        self.full=picture([(32,48)])
        self.cache=policy({'mode':'cold','binding':self.binding,'full':self.full})['cache']
    def req(self,arm,full,hit=True):
        return {'mode':'warm','arm':arm,'binding':self.binding,'cache':self.cache,'full':full,
                'patch':picture([(0,0)] if hit else [],16,16) if arm=='LOCAL_PATCH' else None}
    def test_same_patch_different_global_truth(self):
        full=picture([(32,48),(240,48)])
        self.assertEqual(components(full),[[32,48,16,16],[240,48,16,16]])
        self.assertEqual(policy(self.req('LOCAL_PATCH',None))['point'],[40,56])
        self.assertEqual(policy(self.req('GLOBAL_UNIQUENESS',full))['reason'],'AMBIGUOUS')
    def test_unique(self):
        self.assertEqual(policy(self.req('GLOBAL_UNIQUENESS',self.full))['point'],[40,56])
    def test_absent(self):
        for a in ('LOCAL_PATCH','GLOBAL_UNIQUENESS'):
            self.assertEqual(policy(self.req(a,picture([]),False))['reason'],'ABSENT')
    def test_move_deopts(self):
        out=policy(self.req('LOCAL_PATCH',picture([(240,48)]),False))
        self.assertEqual(out['point'],[248,56]);self.assertEqual(out['scan_pixels'],38656)
    def test_unavailable(self):
        self.assertEqual(policy(self.req('GLOBAL_UNIQUENESS',None))['reason'],'FULL_UNAVAILABLE')
        self.assertEqual(policy(self.req('LOCAL_PATCH',None,False))['reason'],'FULL_UNAVAILABLE')
    def test_generation(self):
        r=json.loads(json.dumps(self.req('LOCAL_PATCH',None)));r['binding']['generation']=2
        self.assertEqual(policy(r)['reason'],'BINDING_MISMATCH')
    def test_bad_abi(self):
        r=picture([(32,48)]);r['depth']=16
        with self.assertRaises(ValueError):components(r)

if __name__=='__main__':unittest.main()
