import pathlib
P=pathlib.Path(__file__).resolve().parent
source=(P/'read_saved.py').read_text(encoding='utf8')
source=source.replace("'wrong-index']","'wrong-index','final-normal','final-O']",1)
source=source.replace('SOURCE_MANIFEST_REPAIRED.json','SOURCE_MANIFEST_FINAL.json')
source=source.replace("('candidate-normal','candidate-O')}","('candidate-normal','candidate-O','final-normal','final-O')}")
source=source.replace("first=data['baseline-first']", "require(data['final-normal']['rows'][:-1]==data['final-O']['rows'][:-1], 'final normal/O equality')\nrequire(data['final-normal']['rows'][:-1]==data['candidate-normal']['rows'][:-1], 'EOF normalization endpoint equality')\nfirst=data['baseline-first']")
source=source.replace('READER_RESULT.json','READER_RESULT_FINAL.json')
(P/'read_saved_final.py').write_bytes(source.encode())
