"""Offline FODS scorer for exactly two numeric cells; never controls the GUI."""
import xml.etree.ElementTree as ET
T='urn:oasis:names:tc:opendocument:xmlns:table:1.0'
O='urn:oasis:names:tc:opendocument:xmlns:office:1.0'
P='urn:oasis:names:tc:opendocument:xmlns:text:1.0'
def q(ns,name): return '{'+ns+'}'+name

def score_saved(blob):
    try:
        root=ET.fromstring(blob)
        sheets=root.findall('.//'+q(T,'table'))
        if len(sheets)!=1: return {'pass_effect':False,'reason':'sheet_count'}
        direct_rows=sheets[0].findall(q(T,'table-row'))
        if len(sheets[0].findall('.//'+q(T,'table-row'))) != len(direct_rows):
            return {'pass_effect':None,'reason':'unsupported_nested_rows'}
        populated=[]; row_index=0
        for row in direct_rows:
            repeat=int(row.get(q(T,'number-rows-repeated'),'1'))
            if repeat<1: raise ValueError('invalid row repetition')
            column=0
            for cell in row:
                if cell.tag not in (q(T,'table-cell'),q(T,'covered-table-cell')): continue
                count=int(cell.get(q(T,'number-columns-repeated'),'1'))
                if count<1: raise ValueError('invalid column repetition')
                value=cell.get(q(O,'value')); formula=cell.get(q(T,'formula'))
                text=''.join(cell.itertext()).strip();kind=cell.get(q(O,'value-type'))
                if value is not None or formula is not None or text or kind is not None:
                    if repeat!=1 or count!=1: return {'pass_effect':False,'reason':'repeated_populated_cell'}
                    populated.append((row_index,column,kind,value,text,formula))
                column+=count
            row_index+=repeat
        expected=[(0,0,'float','731','731',None),(1,0,'float','864','864',None)]
        return {'pass_effect':populated==expected,'populated':populated,'expected':expected}
    except (ET.ParseError,ValueError,TypeError,AttributeError):
        return {'pass_effect':None,'reason':'unreadable_or_invalid_fods'}
