"""Excluded construction and effective semantic corruption checks."""
import copy, hashlib, json, os, tempfile, unittest
from pathlib import Path
from PIL import Image
import audit
from study import Frame, deliver


class Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=None
        if os.environ.get('CONSTRUCTION_OUT'):
            cls.root=Path(os.environ['CONSTRUCTION_OUT']); cls.root.mkdir(parents=True,exist_ok=False)
        else:
            cls.tmp=tempfile.TemporaryDirectory(); cls.root=Path(cls.tmp.name)
        os.sched_setaffinity(0,{0}); Image.init()
        cls.pixels=bytes((i*11+i//7)%256 for i in range(23*17*3))
        cls.frame=Frame(23,17,'RGB',cls.pixels)
        cls.rows=[]
        for rate in (0,65536):
            folder=cls.root/str(rate)
            row=deliver(cls.frame,folder,'construction-'+str(rate),6,rate)
            png=(folder/'producer/001.png').read_bytes()
            cls.rows.append((row,png))

    @classmethod
    def tearDownClass(cls):
        if cls.tmp is not None: cls.tmp.cleanup()

    def test_actual_small_deliveries(self):
        for row,png in self.rows:
            self.assertEqual(audit.decode_png(png),((23,17),self.pixels))
            audit.verify_row(row,png,self.pixels,(23,17),row['id'],6,row['rate'])

    def test_corruptions(self):
        original,png=self.rows[1]
        mutations=[('wrong_level',lambda r:r.update(level=1)),
          ('boolean_level',lambda r:r.update(level=True)),
          ('false_exit',lambda r:r.update(exit=7)),
          ('boolean_exit',lambda r:r.update(exit=False)),
          ('lost_byte',lambda r:r['writes'][0].update(count=r['writes'][0]['count']-1)),
          ('changed_due',lambda r:r['writes'][0].update(due_ns=r['writes'][0]['due_ns']+1)),
          ('decode_clock',lambda r:r['ack'].update(decode_end_ns=r['ack']['decode_start_ns']-1)),
          ('wrong_pixels',lambda r:r['ack'].update(rgb_sha256='0'*64)),
          ('missing_write',lambda r:r['writes'].pop()),
          ('authority',lambda r:r.update(emits_input=True)),
          ('row_length',lambda r:r.update(length=r['length']+1)),
          ('wrong_affinity',lambda r:r.update(parent_affinity=[1]))]
        for name, mutate in mutations:
            with self.subTest(name=name):
                row=copy.deepcopy(original); mutate(row)
                row['ack_wire']=json.dumps(row['ack'],sort_keys=True)+'\n'
                self.assertNotEqual(json.dumps(row,sort_keys=True),json.dumps(original,sort_keys=True))
                with self.assertRaises(ValueError): audit.verify_row(row,png,self.pixels,(23,17),original['id'],6,65536)

    def test_png_crc(self):
        _,png=self.rows[0]; bad=bytearray(png); bad[-5]^=1
        with self.assertRaises(ValueError): audit.decode_png(bytes(bad))

if __name__=='__main__': unittest.main(verbosity=2)
