import subprocess, sys, tempfile, unittest, xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

HERE=Path(__file__).resolve().parent
T='{urn:oasis:names:tc:opendocument:xmlns:table:1.0}'
O='{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'

class AuditRegression(unittest.TestCase):
    def test_extra_populated_cell_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp); (dest/'audit.py').write_bytes((HERE/'audit.py').read_bytes())
            for source in HERE.glob('gg*.zip'):
                with ZipFile(source) as src, ZipFile(dest/source.name,'w',ZIP_DEFLATED) as out:
                    for name in src.namelist():
                        data=src.read(name)
                        if source.name=='gg01.zip' and name=='output/saved.fods':
                            root=ET.fromstring(data); sheet=root.find('.//'+T+'table')
                            row=ET.SubElement(sheet,T+'table-row')
                            ET.SubElement(row,T+'table-cell',{O+'value-type':'float',O+'value':'999'})
                            data=ET.tostring(root,encoding='utf-8',xml_declaration=True)
                        out.writestr(name,data)
            run=subprocess.run([sys.executable,str(dest/'audit.py')],capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0,'audit accepted a saved file with an extra populated cell')
            self.assertIn('vals(z.read',run.stderr)
            self.assertIn('AssertionError',run.stderr)

if __name__=='__main__': unittest.main()
