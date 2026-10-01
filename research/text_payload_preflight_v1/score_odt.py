"""Post-execution durable scorer; never imported by the input executor."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

TEXT='urn:oasis:names:tc:opendocument:xmlns:text:1.0'

def contents(node):
    value=node.text or ''
    for child in node:
        if child.tag == '{'+TEXT+'}s': value += ' '*int(child.get('{'+TEXT+'}c','1'))
        elif child.tag == '{'+TEXT+'}tab': value += '\t'
        elif child.tag == '{'+TEXT+'}line-break': value += '\n'
        else: value += contents(child)
        value += child.tail or ''
    return value

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('path',type=Path); ap.add_argument('--expected',required=True); a=ap.parse_args()
    raw=a.path.read_bytes()
    with zipfile.ZipFile(a.path) as z:
        bad=z.testzip()
        root=ET.fromstring(z.read('content.xml'))
        paragraphs=[contents(p) for p in root.findall('.//{'+TEXT+'}p')]
    print(json.dumps({'actual':paragraphs,'expected':[a.expected], 'exact':paragraphs==[a.expected],
                      'zip_crc_ok':bad is None,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}, ensure_ascii=True))

if __name__=='__main__': main()
