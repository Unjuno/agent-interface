import csv,io,math,re
REGIONS={'A1':(20,180,125,200),'A2':(20,200,125,220)}
EXPECTED={'A1':'731','A2':'864'}
def cell_pair_cue(tsv,*,main_sheet_reviewed,modal_present):
    # Historical known-task development cue. No scope, freshness or authority.
    if main_sheet_reviewed is not True or modal_present is not False:return 'unknown'
    found={name:[] for name in REGIONS}
    try:
        rows=list(csv.DictReader(io.StringIO(tsv),delimiter='\t'))
        for row in rows:
            text=row.get('text','').strip()
            if not text:continue
            box=tuple(int(row[k]) for k in ['left','top','width','height'])
            x,y,w,h=box;confidence=float(row['conf'])
            if w<=0 or h<=0 or not math.isfinite(confidence) or not 0<=confidence<=100:return 'unknown'
            owners=[name for name,(l,t,r,b) in REGIONS.items() if x>=l and y>=t and x+w<=r and y+h<=b]
            if len(owners)>1:return 'unknown'
            if owners:
                if confidence<90 or not re.fullmatch(r'[0-9]+',text):return 'unknown'
                found[owners[0]].append(text)
    except (ValueError,KeyError,TypeError,AttributeError):return 'unknown'
    if any(len(values)!=1 for values in found.values()):return 'unknown'
    return 'filled' if all(found[name]==[value] for name,value in EXPECTED.items()) else 'wrong'
