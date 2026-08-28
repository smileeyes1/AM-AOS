from __future__ import annotations
import json, sqlite3, threading
from pathlib import Path
from typing import Any
from .runtime import digest

class SQLiteStore:
    """Backward-compatible durable store plus integrity checks."""
    def __init__(self,path=':memory:'):
        self.path=path; self.db=sqlite3.connect(path,check_same_thread=False); self._lock=threading.RLock(); self.db.execute('PRAGMA foreign_keys=ON'); self.db.execute('PRAGMA journal_mode=WAL' if path != ':memory:' else 'PRAGMA journal_mode=MEMORY'); self.db.execute('PRAGMA synchronous=FULL'); self.db.executescript('CREATE TABLE IF NOT EXISTS missions(mission_id TEXT PRIMARY KEY,goal TEXT NOT NULL,contract_json TEXT NOT NULL,contract_hash TEXT NOT NULL); CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT UNIQUE NOT NULL,event_hash TEXT NOT NULL,payload_json TEXT NOT NULL); CREATE TABLE IF NOT EXISTS evidence(evidence_id TEXT PRIMARY KEY,task_id TEXT NOT NULL,digest TEXT NOT NULL,payload_json TEXT NOT NULL,sufficient INTEGER NOT NULL CHECK(sufficient IN(0,1)));'); self.db.commit()
    def save_mission(self,mission_id,goal,contract,contract_hash):
        with self._lock,self.db: self.db.execute('INSERT INTO missions VALUES(?,?,?,?)',(mission_id,goal,json.dumps(contract,sort_keys=True,ensure_ascii=False),contract_hash))
    def mission_contract_hash(self,mission_id):
        row=self.db.execute('SELECT contract_hash FROM missions WHERE mission_id=?',(mission_id,)).fetchone()
        if not row: raise KeyError(mission_id)
        return row[0]
    def append_event(self,event_id,event_hash,payload):
        with self._lock,self.db: self.db.execute('INSERT INTO events(event_id,event_hash,payload_json) VALUES(?,?,?)',(event_id,event_hash,json.dumps(payload,sort_keys=True,ensure_ascii=False,default=str)))
    def count_events(self): return self.db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    def verify_integrity(self):
        for _,_,text,h in self.db.execute('SELECT mission_id,goal,contract_json,contract_hash FROM missions'):
            if not h: return False
        for _,h,text in self.db.execute('SELECT event_id,event_hash,payload_json FROM events'):
            if not h: return False
        return True
    def close(self): self.db.close()

class Store(SQLiteStore):
    """Production-oriented name for the durable store boundary."""
    def __init__(self,path='data/am_aos.sqlite3'): super().__init__(path)
