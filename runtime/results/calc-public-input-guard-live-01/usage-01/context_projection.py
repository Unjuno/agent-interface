import json,hashlib
FIELDS=('turn_id','model','effort')
def project_context(line):
 row=json.loads(line)
 if row.get('type')!='turn_context':raise ValueError('context projection applies only to turn_context')
 row['payload']={k:row['payload'].get(k) for k in FIELDS}
 return json.dumps(row)+'\n'
def original_matches(record,line):
 if record.get('privacy_projection') is not None:
  return (record['privacy_projection']=={'kind':'turn_context_metadata','payload_fields':list(FIELDS)}
          and hashlib.sha256(line.encode()).hexdigest()==record['original_raw_sha256']
          and project_context(line)==record['raw_line'])
 return line==record['raw_line']
