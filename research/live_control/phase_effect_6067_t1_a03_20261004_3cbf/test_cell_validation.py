import copy
import unittest
from pathlib import Path
from cell_validation import validate_cell
import reference as ref

ROOT=Path(__file__).resolve().parent.parent/'source_deadline_probe_6067_b01_20261003_3cbf/native-raw/record'
SPEC={'id':'b000','kind':'pulse','schedule':'fixed','offsets':[0,0,0,0],'phase':0,'width_ms':20}

def saved():
    return {'source':ref.read(ROOT/'source.json'),'capture':ref.read(ROOT/'capture.json'),
            'lifecycle':ref.read(ROOT/'cell.json')['lifecycle'],
            'source_journal':[ref.parse_record(s) for s in (ROOT/'source.jsonl').read_text().splitlines()],
            'source_waits':[ref.parse_record(s) for s in (ROOT/'source-waits.jsonl').read_text().splitlines()],
            'frames':[ref.parse_record(s) for s in (ROOT/'frames.jsonl').read_text().splitlines()],
            'observer_waits':[ref.parse_record(s) for s in (ROOT/'waits.jsonl').read_text().splitlines()]}

class Cells(unittest.TestCase):
    def test_historical_saved_cell_validates_without_native_replay(self):
        got=validate_cell(SPEC,saved())
        self.assertEqual(got['source_waits_checked'],16)
        self.assertEqual(got['captures_checked'],8)
        self.assertEqual(got['stable_ids'],list(range(1,9)))
    def test_joined_boolean_deadline_is_rejected(self):
        cell=saved()
        for trace in (cell['source']['wait_traces'][0],cell['source_waits'][0]):trace['due_ns']=False
        with self.assertRaises(ValueError):validate_cell(SPEC,cell)
    def test_missing_wait_is_rejected_even_when_both_copies_changed(self):
        cell=saved();cell['source']['wait_traces'].pop();cell['source_waits'].pop()
        with self.assertRaises(ValueError):validate_cell(SPEC,cell)
    def test_raw_frame_journal_is_required(self):
        cell=saved();cell['frames'].pop()
        with self.assertRaises(ValueError):validate_cell(SPEC,cell)
    def test_historical_lateness_gate_remains(self):
        cell=saved();cell['capture']['frames'][0]['start_ns']+=11_000_000
        cell['frames']=copy.deepcopy(cell['capture']['frames'])
        with self.assertRaises(ValueError):validate_cell(SPEC,cell)
    def test_source_and_observer_journal_corruption_rejected(self):
        for kind in ('source_journal','observer_waits'):
            cell=saved()
            if kind=='source_journal':cell[kind][0]['id']=99
            else:cell[kind][0]['index']=99
            with self.assertRaises(ValueError):validate_cell(SPEC,cell)
    def test_joined_source_wait_post_after_paint_rejected(self):
        cell=saved()
        for t in (cell['source']['wait_traces'][0],cell['source_waits'][0]):
            t['post']['end_ns']=cell['source']['events'][0]['draw_start_ns']+1
        with self.assertRaises(ValueError):validate_cell(SPEC,cell)
    def test_joined_process_counter_regression_rejected(self):
        cell=saved()
        for t in (cell['source']['wait_traces'][2],cell['source_waits'][2]):
            for s in ('pre','post'):t[s]['process_cpu_ns']=0
        with self.assertRaises(ValueError):validate_cell(SPEC,cell)

if __name__=='__main__':unittest.main()
