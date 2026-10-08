"""Host-side custody gate for prospective controller relay. No provider calls."""
from pathlib import Path,PurePosixPath
import json,hashlib

def verify_local_images(message,output_root):
 root=Path(output_root).resolve(strict=True)
 if message.get('method')!='turn/start':return []
 verified=[]
 for item in message.get('params',{}).get('input',[]):
  if item.get('type')!='localImage':continue
  supplied=item.get('path')
  if not isinstance(supplied,str) or not Path(supplied).is_absolute():raise ValueError('image requires absolute host path')
  path=Path(supplied).resolve(strict=True)
  relative=path.relative_to(root).as_posix()
  if not path.is_file():raise ValueError('image is not a file')
  receipt_file=root/'image-path-receipts.jsonl'
  receipts=[json.loads(line) for line in receipt_file.read_text().splitlines() if line.strip()]
  candidates=[r for r in receipts if r.get('relative_path')==relative and Path(r.get('host_path','')).resolve()==path]
  if not candidates:raise ValueError('missing matching guest custody receipt')
  receipt=candidates[-1]
  if PurePosixPath(receipt['relative_path']).is_absolute() or '..' in PurePosixPath(receipt['relative_path']).parts:raise ValueError('unsafe relative path')
  raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
  if digest!=receipt.get('sha256') or len(raw)!=receipt.get('bytes'):raise ValueError('host image does not match guest receipt')
  verified.append({'host_path':str(path),'relative_path':relative,'sha256':digest,'bytes':len(raw),'scope':'host file bytes at forwarding check; no provider decoded-byte receipt'})
 return verified
