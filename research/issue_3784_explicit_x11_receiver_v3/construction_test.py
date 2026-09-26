"""Pre-formal validation of receiver control and the complete XKB parser/map gate."""
from pathlib import Path
import unittest
import runner

class Construction(unittest.TestCase):
    def test_de_transition_and_us_nonmutation(self):
        source=Path("/repo")
        helper=runner.helpers(source)
        de=runner.construction_case(":227","de",True,helper)
        us=runner.construction_case(":228","us",False,helper)
        self.assertEqual(de.get("status"),"PASS_CONSTRUCTION",de)
        self.assertTrue(de.get("focus_ok"))
        self.assertTrue(de.get("control_ok"))
        self.assertTrue(de.get("baseline",{}).get("layout_ok"))
        self.assertTrue(de.get("after",{}).get("layout_ok"))
        self.assertEqual(de.get("apply",{}).get("argv"),["setxkbmap","-layout","de"])
        self.assertTrue(de.get("map_gate_ok"))
        self.assertNotEqual(de["baseline"]["map_sha256"],de["after"]["map_sha256"])
        self.assertEqual(us.get("status"),"PASS_CONSTRUCTION",us)
        self.assertEqual(us["baseline"]["map_sha256"],us["after"]["map_sha256"])

if __name__=="__main__":unittest.main()
