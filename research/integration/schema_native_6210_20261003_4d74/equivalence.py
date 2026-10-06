import json,pathlib
from surface import decode,program
count=0
for x in range(640):
 for y in range(360):
  a=decode(dict(action='click',x=x,y=y),'A');b=decode(dict(operation='pointer_select',horizontal=x,vertical=y),'B')
  assert a==b==(x,y) and program(*a,123)==program(*b,123);count+=1
bad=[(-1,2),(640,2),(1,360),(True,2),(1,False),(1.0,2)]
for x,y in bad:
 for v,p in [('A',dict(action='click',x=x,y=y)),('B',dict(operation='pointer_select',horizontal=x,vertical=y))]:
  try:decode(p,v)
  except ValueError:pass
  else:raise AssertionError('invalid coordinate accepted')
assert decode(dict(action='click',x=100,y=180),'A')!=decode(dict(operation='pointer_select',horizontal=180,vertical=100),'B')
print(json.dumps(dict(status='PASS_BIJECTIVE_CANONICAL_PROGRAM_MAPPING',coordinates=count,invalid_encodings=12,negative_swapped_axis_rejected=True,scope='output-response schema mapping, not provider function tools or arbitrary runtime proof')))
