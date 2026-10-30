"""Classify two already-produced cell OCR TSVs; grants no input authority."""
import csv,io,math,re

def _read(tsv):
    try:
        reader=csv.DictReader(io.StringIO(tsv),delimiter='\t')
        if reader.fieldnames is None or not {'level','conf','text'}.issubset(reader.fieldnames): return None
        values=[]
        for row in reader:
            text=(row.get('text') or '').strip()
            if not text: continue
            if row.get('level')!='5': return None
            confidence=float(row['conf'])
            if not math.isfinite(confidence) or not 90<=confidence<=100 or not re.fullmatch('[0-9]+',text): return None
            values.append(text)
        return values[0] if len(values)==1 else None
    except (ValueError,TypeError,KeyError,csv.Error): return None

def classify(a1_tsv,a2_tsv):
    a,b=_read(a1_tsv),_read(a2_tsv)
    if a is None or b is None: return 'unknown'
    return 'filled' if (a,b)==('731','864') else 'wrong'
