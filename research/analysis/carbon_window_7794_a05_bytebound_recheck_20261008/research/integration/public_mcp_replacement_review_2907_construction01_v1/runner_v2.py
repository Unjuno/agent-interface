"""Additive response-shape adapter for a fresh construction02 invocation."""
import json
from pathlib import Path
import runner as predecessor

def normalize_public_receipt(result):
    texts=[x.text for x in result.content if getattr(x,'type',None)=='text']
    if len(texts)!=1: raise RuntimeError('MCP_TEXT_CARDINALITY')
    payload=json.loads(texts[0])
    if payload.get('schema')!='agent-interface/review-v1': return payload
    receipt=payload.get('receipt',{}); raw=receipt.get('source',{}).get('raw_report',{})
    if receipt.get('schema')!='agent-interface/receipt-view-v1' or not isinstance(raw,dict):
        raise RuntimeError('PUBLIC_RECEIPT_SHAPE_UNRECOGNIZED')
    payload['status']=raw.get('status')
    payload['observation']=raw
    payload['input_dispatched']=raw.get('input_dispatched')
    payload['side_effect_authority']=raw.get('side_effect_authority')
    payload['session']=payload.get('session') or raw.get('session')
    return payload

predecessor.getpayload=normalize_public_receipt
predecessor.OUT=Path('/evidence/construction02')

if __name__=='__main__': raise SystemExit(predecessor.main())

