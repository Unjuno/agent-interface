import json, unittest, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from audit_navigation_stages import RESULT_ROOT
class NavigationStageArtifactTests(unittest.TestCase):
    def test_all_manual_labels_bind_to_contiguous_retained_frames(self):
        labels=json.loads((HERE/'ANNOTATIONS.json').read_text())['frames']; manifest=json.loads((RESULT_ROOT/'frame-manifest.json').read_text())
        self.assertEqual(len(labels),13); self.assertEqual([x['iteration'] for x in labels],list(range(13)))
        self.assertEqual([(x['file'],x['sha256']) for x in labels],[(x['file'],x['sha256']) for x in manifest])
        self.assertTrue(all(x.get('stage') and x.get('cue') for x in labels))
    def test_raw_audit_reconstructs_command_and_terminal_boundary(self):
        audit=json.loads((HERE/'AUDIT.json').read_text())
        self.assertEqual(audit['disposition'],'PASS_SCOPED_VIEWPOINT_STAGES_HOLD_EXACT_ROUTE')
        self.assertEqual((audit['primary_command_receipts_recomputed'],audit['visible_change_receipts_recomputed'],audit['no_visible_effect_receipts_recomputed']),(26,25,1))
        self.assertEqual((audit['contingencies_authored_recomputed'],audit['contingency_branches_taken_recomputed']),(8,0))
        self.assertEqual(audit['terminal'],{'map_exit':False,'player_dead':True,'kill_count':1})
if __name__=='__main__': unittest.main()
