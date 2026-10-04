import builtins
import unittest
from unittest.mock import patch
from candidate import planned_rows, inject


class CandidateTests(unittest.TestCase):
    def test_eight_balanced_unique_cells(self):
        rows=planned_rows({'seed':52607026,'replicates_per_cell':2})
        self.assertEqual(len(rows),8)
        self.assertEqual(sum(r['instrumentation_mode']=='MEMORY_ONLY' for r in rows),4)
        self.assertEqual(sum(r['instrumentation_mode']=='SYNC_FILE' for r in rows),4)
        self.assertEqual(sum(r['load']=='cpu_busy' for r in rows),4)
        self.assertEqual(len({tuple(sorted(row.items())) for row in rows}),8)

    def test_readiness_refusal_precedes_xlib_import_or_input(self):
        original=builtins.__import__
        imports=[]
        def observe(name,*args,**kwargs):
            if name.startswith('Xlib'):imports.append(name)
            return original(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=observe):
            with self.assertRaises(RuntimeError):
                inject({}, {'instrumentation_mode':'MEMORY_ONLY'}, {})
        self.assertEqual(imports,[])


if __name__=='__main__':unittest.main()
