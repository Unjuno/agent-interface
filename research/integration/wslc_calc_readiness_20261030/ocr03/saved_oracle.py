import hashlib,json,xml.etree.ElementTree as E
N={'t':'urn:oasis:names:tc:opendocument:xmlns:table:1.0','o':'urn:oasis:names:tc:opendocument:xmlns:office:1.0','p':'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}
def score_saved(blob,a,b):
 table=E.fromstring(blob).find('.//t:table',N);populated=[];ri=0
 for row in table.findall('t:table-row',N):
  repeat=int(row.get('{'+N['t']+'}number-rows-repeated','1'));ci=0
  for cell in row:
   if cell.tag not in ('{'+N['t']+'}table-cell','{'+N['t']+'}covered-table-cell'):continue
   count=int(cell.get('{'+N['t']+'}number-columns-repeated','1'));text=''.join(cell.itertext()).strip();value=cell.get('{'+N['o']+'}value');formula=cell.get('{'+N['t']+'}formula')
   if text or value or formula:
    if repeat>1 or count>1:raise ValueError('unexpected repeated populated cells')
    populated.append((ri,ci,text,value,formula))
   ci+=count
  ri+=repeat
 expected=[(0,0,'a',None,None),(0,1,'b',None,None),(0,2,'product',None,None),(1,0,str(a),str(a),None),(1,1,str(b),str(b),None),(1,2,str(a*b),str(a*b),'of:=[.A2]*[.B2]')]
 return dict(pass_effect=populated==expected,populated=populated,expected=expected)
def score_done(root,row):
 blob=(root/(row['label']+'.fods')).read_bytes();result=score_saved(blob,row['a'],row['b']);errors=[]
 if not result['pass_effect']:errors.append('saved effect or collateral cell content')
 if hashlib.sha256(blob).hexdigest()!=row['saved_sha256']:errors.append('saved file digest')
 if row['receipt']['status']!='completed' or row['receipt'].get('recovery_required'):errors.append('public receipt completion')
 if row['physical']['keys'] or row['physical']['buttons']:errors.append('physical neutral')
 artifact=row['image']['image']['artifact'];png=root/'images'/artifact['path'].rsplit('/',1)[-1]
 if hashlib.sha256(png.read_bytes()).hexdigest()!=artifact['sha256']:errors.append('original final PNG digest')
 return dict(errors=errors,effect=result)
