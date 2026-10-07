"""Real Tk callback wiring construction; not XTest/recovery evidence."""
import json
import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch
import app
from task_file_audit import file_errors

@unittest.skipUnless(os.environ.get('DISPLAY'),'private Linux X display required')
class AppSaveTests(unittest.TestCase):
    def test_save_button_writes_actual_target_value(self):
        real_tk=tk.Tk
        with tempfile.TemporaryDirectory() as directory:
            read_fd,write_fd=os.pipe()
            def create_root():
                root=real_tk()
                def exercise():
                    entries=[w for w in root.winfo_children() if isinstance(w,tk.Entry)]
                    entries[1].insert(0,'http://m_n')
                    next(w for w in root.winfo_children() if isinstance(w,tk.Button)).invoke()
                root.after(300,exercise)
                return root
            try:
                with patch.object(app.tk,'Tk',create_root), patch.object(app,'__file__',
                        str(Path(__file__).parent/'gui_construction'/'app.py')):
                    self.assertEqual(app.main(directory,'construction-a12','MEMORY_ONLY',write_fd),0)
                output=Path(directory)/'task_result.json'
                self.assertTrue(output.exists(),'Save callback must create ordinary task file')
                value=json.loads(output.read_bytes())
                self.assertEqual(value['text'],'http://m_n')
                record=json.loads((Path(directory)/'app_result.json').read_bytes())
                self.assertEqual(record['save_count'],1)
                self.assertEqual(record['task_file']['path'],'task_result.json')
                self.assertEqual(file_errors(directory,{'app':record,'app_pid':record['pid'],
                    'token':'construction-a12'},'http://m_n'),[])
            finally:
                os.close(read_fd)
                try:os.close(write_fd)
                except OSError:pass

if __name__=='__main__':unittest.main()
