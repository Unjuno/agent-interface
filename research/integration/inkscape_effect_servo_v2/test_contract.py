import json,tempfile,unittest
from pathlib import Path
import numpy as np
from PIL import Image
import audit
class T(unittest.TestCase):
    def test_schedule(self):
        s=json.loads((Path(__file__).parent/'SCHEDULE.json').read_text())['cases'];self.assertEqual(len(s),12);self.assertEqual(len({x['index'] for x in s}),12)
    def test_residual_arithmetic(self):
        self.assertEqual([30+(50-25),18+(30-15)],[55,33]);self.assertEqual([30+(50-20),18+(30-12)],[60,36])
    def test_red_component(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'a.png';a=np.zeros((800,1280,3),dtype=np.uint8);a[300:330,400:440,0]=255;Image.fromarray(a).save(p);self.assertEqual(audit.red_components(p),[[400,300,440,330]])
if __name__=='__main__':unittest.main()
