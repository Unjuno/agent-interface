import base64,datetime,gzip,hashlib,json,pathlib
P=pathlib.Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
prior=P.parent/'x11-sidebutton-construction-01a0ff2c'
(P/'PUBLIC_DEPENDENCIES.json').write_bytes((prior/'PUBLIC_DEPENDENCIES.json').read_bytes())
freeze=json.loads((P/'freeze-final/FREEZE.json').read_text(encoding='utf8'))
fixed=['REPORT.md','READER_RESULT_FINAL.json','SOURCE_MANIFEST_FINAL.json','REMOTE_SOURCE_READBACK.json','PUBLIC_DEPENDENCIES.json']
proposal={'policy_version':'FINAL-v5','repository':'Unjuno/agent-interface','worker_id':'01a0ff2c-34fb-73a0-b3aa-bdf13badf325','change_id':'x11-unified-custody-v4-xi2-sidebuttons','head_sha':'ed7bb24e45fac16114e1247e00c8ed86cebda5c8','tree_sha':freeze['tree'],'parent_sha':freeze['parent'],'review_base_sha':freeze['review_base'],'images':freeze['images'],'diff':freeze['full_diff'],'delta_from_V3':freeze['delta_from_V3'],'committee_epoch':'x11-unified-custody-v4-xi2-source-before-votes','prospective_nonauthors':['01a0ff53-0975-79e2-8d4e-d28683bc4f8e','01a0ff58-480b-7d50-9eee-0bce12250476','01a0ff58-ba92-7fd2-9317-d75b43383005'],'threshold':2,'acceptance_required':True,'previous_votes_transfer':0,'evidence':{name:{'bytes':(P/name).stat().st_size,'sha256':sha((P/name).read_bytes())} for name in fixed},'source_images':32,'selected_methods':57,'endpoints':176,'dependencies':'PUBLIC_DEPENDENCIES.json','conditions':['Exact fixed source and test definitions/dependency pins','Selected inert source behavior only; no whole workflow/harness/native/current-main qualification inferred','Adoption/application HOLD pending native ClientPointer/device-topology/physical-input qualification and required nonauthor whole planned-tree checks','No main authority, sender, lease or resource allocation supplied by this source proposal','Previous V3/V2 votes and nominations provide zero new approvals'],'goal':'Broad computer-control goal active and incomplete'}
canonical=json.dumps(proposal,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
(P/'PROPOSAL.json').write_bytes(canonical)
(P/'PROPOSAL_PIN.json').write_bytes((json.dumps({'bytes':len(canonical),'sha256':sha(canonical),'head':proposal['head_sha'],'tree':proposal['tree_sha'],'epoch':proposal['committee_epoch']},indent=2)+'\n').encode())
pub=P/'public';pub.mkdir(exist_ok=False)
originals={};members={};omissions={}
workspace=str(P.parents[1]);interpreter=r'<PYTHON312>'
for f in sorted(P.rglob('*')):
    if not f.is_file() or f.is_relative_to(pub):continue
    rel=f.relative_to(P).as_posix();raw=f.read_bytes()
    originals[rel]={'bytes':len(raw),'sha256':sha(raw)}
    if f.name=='source.index' or len(raw)>1_000_000:
        omissions[rel]={**originals[rel],'reason':'isolated Git index or full source-tree inventory; original retained locally, exact Git tree refs and all changed/imported full images recoverable'}
        continue
    try:
        text=raw.decode('utf8')
        for old,new in [(workspace,'<WORKSPACE>'),(workspace.replace('\\','/'),'<WORKSPACE>'),(interpreter,'<PYTHON312>')]:
            text=text.replace(old,new).replace(old.replace('\\','\\\\'),new)
        projected=text.encode()
    except UnicodeDecodeError:projected=raw
    members[rel]={'bytes':len(projected),'sha256':sha(projected),'base64':base64.b64encode(projected).decode(),'projected':projected!=raw,'original':originals[rel]}
packet={'format':'data-only-evidence-v1','members':members,'original_manifest':originals,'explicit_omissions':omissions,'projection':'workspace/interpreter literals removed from public text only; original stream hashes describe retained original bytes and do not authenticate private provenance; do not execute received scripts'}
raw=json.dumps(packet,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0)
(pub/'packet.json').write_bytes(raw);(pub/'packet.gz').write_bytes(compressed)
meta={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'members':len(members),'omissions':len(omissions),'json_bytes':len(raw),'json_sha256':sha(raw),'gzip_bytes':len(compressed),'gzip_sha256':sha(compressed),'proposal_bytes':len(canonical),'proposal_digest':sha(canonical)}
(pub/'META.json').write_bytes((json.dumps(meta,indent=2)+'\n').encode())
b64=base64.b64encode(compressed).decode();chunks=[b64[i:i+48000] for i in range(0,len(b64),48000)]
for i,chunk in enumerate(chunks,1):
    text='Author34fb / FINAL-v5 / fixed7148V4 DATA-only proof part'+str(i)+'/'+str(len(chunks))+'. Concatenate ordered base64; decode gzip/JSON and verify all member lengths/SHA before reading. Never execute received scripts. Packet metadata '+json.dumps(meta)+'. Original paths are explicitly projected; omitted Git inventories/indexes are pinned and retained, all scientific first failures/source/actor streams/controls included. Native/current-main/adoption HOLD; no votes/main authority.\n\n```base64\n'+chunk+'\n```\n'
    (pub/f'COMMENT-{i}.txt').write_bytes(text.encode())
print(json.dumps(meta|{'comments':len(chunks)}))
