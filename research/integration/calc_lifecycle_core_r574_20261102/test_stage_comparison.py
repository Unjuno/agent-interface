import hashlib, io, json, tempfile, unittest, zipfile
from pathlib import Path
from stage_comparison import stage_archive, _validate_names


def archive(*, corrupt=False, traversal=False):
    data=io.BytesIO()
    with zipfile.ZipFile(data,'w') as z:
        for i, route in enumerate(('direct','compiled','fresh'),1):
            name='../escape' if traversal else 'runner.py'
            content=('runner-'+route).encode()
            expected=hashlib.sha256(content).hexdigest()
            c={'allocation':'eq%02d'%i,'route':route,'values':['472','615'],
               'input_sha256':{name:expected}}
            z.writestr('eq%02d/conditions.json'%i,json.dumps(c))
            z.writestr('eq%02d/'%i+name, b'bad' if corrupt and i==2 else content)
    return data.getvalue()


class StageTests(unittest.TestCase):
    def test_stages_reviewed_inputs_and_records_different_route_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bundle'
            receipt=stage_archive(archive(),path,commit='a'*40)
            self.assertEqual((path/'inputs'/'runner.py').read_bytes(),b'runner-direct')
            self.assertEqual(len(set(receipt['route_input_hashes'][x]['runner.py'] for x in ('direct','compiled','fresh'))),3)
            self.assertEqual(json.loads((path/'manifest.json').read_text()),receipt)

    def test_corruption_or_unsafe_path_produces_no_bundle(self):
        with tempfile.TemporaryDirectory() as d:
            for blob in (archive(corrupt=True),archive(traversal=True)):
                path=Path(d)/'bundle'
                with self.assertRaises(ValueError):stage_archive(blob,path,commit='a'*40)
                self.assertFalse(path.exists())

    def test_windows_aliases_and_file_directory_collisions_are_rejected(self):
        for names in (['CON.txt'], ['part.'], ['space '], ['A.py','a.py'],
                      ['folder','folder/file.py'], ['bad?.py']):
            with self.subTest(names=names), self.assertRaises(ValueError):
                _validate_names(names)

    def test_existing_target_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'bundle';path.mkdir();(path/'keep').write_text('keep')
            with self.assertRaises(FileExistsError):stage_archive(archive(),path,commit='a'*40)
            self.assertEqual((path/'keep').read_text(),'keep')

if __name__=='__main__':unittest.main()
