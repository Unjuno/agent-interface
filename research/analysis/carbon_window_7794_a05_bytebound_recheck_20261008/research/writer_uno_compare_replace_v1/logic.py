from __future__ import annotations

def classify_candidate(count:int, final:str)->str:
    if count == 0 and final == 'bookx': return 'APPEND_THEN_REPLACE_NO_MATCH'
    if count == 1 and final == 'bookkeeperofficex': return 'REPLACE_THEN_APPEND'
    return 'UNSAFE_OR_UNEXPECTED'

def gate(condition:str, count:int|None, final:str, refused:bool=False)->bool:
    if condition == 'baseline_gap': return (not refused) and final == 'bookkeeperoffice'
    if condition == 'append_then_replace': return (not refused) and classify_candidate(int(count), final) == 'APPEND_THEN_REPLACE_NO_MATCH'
    if condition == 'replace_then_append': return (not refused) and classify_candidate(int(count), final) == 'REPLACE_THEN_APPEND'
    if condition.startswith('race_'): return (not refused) and classify_candidate(int(count), final) != 'UNSAFE_OR_UNEXPECTED'
    if condition == 'stale_uid': return refused and final == 'book'
    return False
