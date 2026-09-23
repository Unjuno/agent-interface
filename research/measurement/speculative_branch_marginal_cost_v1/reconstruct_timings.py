import base64,hashlib,json,lzma,pathlib,struct
p=pathlib.Path('.')
m=json.loads((p/'RAW_TIMINGS_PACKING.json').read_text())
xz=base64.b64decode(''.join((p/x).read_text().strip() for x in m['parts']))
assert len(xz)==m['xz_bytes'] and hashlib.sha256(xz).hexdigest()==m['xz_sha256']
b=lzma.decompress(xz); assert len(b)==m['packed_bytes'] and hashlib.sha256(b).hexdigest()==m['packed_sha256']
assert b[:6]==b'SBMC1\0'; n=struct.unpack_from('<Q',b,6)[0]; assert n==m['pairs']
o=14; k1=list(struct.unpack_from('<%dQ'%n,b,o)); o+=8*n; k2=list(struct.unpack_from('<%dQ'%n,b,o)); o+=8*n; assert o==len(b)
raw={'task':'SPECULATIVE-BRANCH-MARGINAL-PREP-COST-20260918-001','seed':117320260918001,'pairs':n,'k1_ns':k1,'k2_ns':k2,'marginal_ns':[b-a for a,b in zip(k1,k2)]}
rb=(json.dumps(raw,separators=(',',':'))+'\n').encode(); assert len(rb)==m['original_raw_json_bytes'] and hashlib.sha256(rb).hexdigest()==m['original_raw_json_sha256']
(p/'RAW_TIMINGS.reconstructed.json').write_bytes(rb); print(m['original_raw_json_sha256'])
