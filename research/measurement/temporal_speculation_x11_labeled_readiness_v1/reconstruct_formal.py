from pathlib import Path
import lzma
p=Path(__file__).parent
raw=lzma.decompress((p/"FORMAL_RESULT.json.xz").read_bytes())
(p/"FORMAL_RESULT.json").write_bytes(raw)
print(p/"FORMAL_RESULT.json")
