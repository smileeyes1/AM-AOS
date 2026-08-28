from __future__ import annotations
import json, sqlite3, threading
from pathlib import Path
from typing import Any
from .runtime import canonical, digest

class Store:
    """SQLite persistence with transactional writes and integrity checks."""
    def __init__(self,path='data/am_aos.sqlite3'):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True); self._lock=threading.RLock(); self.db=sqlite3.connect(self.path,check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL'); self.db.execute('PRAGMA foreign_keys=ON'); self.db.execute('PRAGMA synchronous=FULL'); self._init()
    def _init(self):
        with self.db:
            self.db.executescript('''CREATE TABLE IF NOT EXISTS missions(id TEXT PRIMARY KEY, payload TEXT NOT NULL, digest TEXT NOT NULL); CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, mission_id TEXT NOT NULL REFERENCES missions(id), payload TEXT NOT NULL, digest TEXT NOT NULL); CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id), payload TEXT NOT NULL, digest TEXT NOT NULL); CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL, digest TEXT NOT NULL);''')
    def put(self,table,key,payload,ref=None):
        d=digest(payload); text=json.dumps(payload,ensure_ascii=False,sort_keys=True,default=str)
        with self._lock,self.db:
            if table=='missions': self.db.execute('INSERT OR REPLACE INTO missions(id,payload,digest) VALUES(?,?,?)',(key,text,d))
            elif table=='tasks': self.db.execute('INSERT OR REPLACE INTO tasks(id,mission_id,payload,digest) VALUES(?,?,?,?)',(key,ref,text,d))
            elif table=='evidence': self.db.execute('INSERT OR REPLACE INTO evidence(id,task_id,payload,digest) VALUES(?,?,?,?)',(key,ref,text,d))
            else: raise ValueError('unsupported table')
        return d
    def append_audit(self,payload):
        text=json.dumps(payload,ensure_ascii=False,sort_keys=True,default=str); d=digest(payload)
        with self._lock,self.db: self.db.execute('INSERT INTO audit(payload,digest) VALUES(?,?)',(text,d))
        return d
    def verify(self):
        with self._lock:
            for table in ('missions','tasks','evidence'):
                for _,text,d in self.db.execute(f'SELECT id,payload,digest FROM {table}'):
                    if digest(json.loads(text))!=d: return False
            return True
    def close(self): self.db.close()
