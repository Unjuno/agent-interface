from __future__ import annotations
from dataclasses import dataclass
import sqlite3

@dataclass(frozen=True)
class Receipt:
    key: str
    revision: int

class ReadTracker:
    def __init__(self, conn: sqlite3.Connection):
        self.conn=conn; self.receipts:list[Receipt]=[]
    def read(self,key:str)->str:
        row=self.conn.execute('select value,revision from kv where key=?',(key,)).fetchone()
        if row is None: raise KeyError(key)
        value,rev=row; self.receipts.append(Receipt(key,int(rev))); return str(value)

def decide(conn:sqlite3.Connection, mode:str):
    tracker=ReadTracker(conn)
    a=tracker.read('A')
    if mode=='tracked':
        b=tracker.read('B')
    elif mode=='bypass':
        row=conn.execute("select value from kv where key='B'").fetchone()
        if row is None: raise KeyError('B')
        b=str(row[0])
    else: raise ValueError(mode)
    return a+'|'+b, tracker.receipts
