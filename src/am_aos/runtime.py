from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from hashlib import sha256
from typing import Any, Callable
import json,time
from uuid import uuid4
class Decision(str,Enum):
 PASS='PASS'; CONDITIONAL_PASS='CONDITIONAL PASS'; FAIL='FAIL'; NO_GO='NO-GO'; NOT_PROVEN='NOT PROVEN'; INCONCLUSIVE='INCONCLUSIVE'; BLOCKED='BLOCKED'
class EvidenceState(str,Enum):
 UNREPORTED='UNREPORTED'; REPORTED='REPORTED'; REPRODUCIBLE='REPRODUCIBLE'; VERIFIED='VERIFIED'; INDEPENDENTLY_VERIFIED='INDEPENDENTLY VERIFIED'; EXTERNALLY_INDEPENDENT='EXTERNALLY INDEPENDENT'
def canonical(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,default=str,separators=(',',':')).encode()
def digest(v): return sha256(canonical(v)).hexdigest()
@dataclass(frozen=True)
class MissionContract: mission_id:str; goal:str; acceptance_criteria:tuple[str,...]; constraints:tuple[str,...]; authorities:frozenset[str]; scope:str; frozen_at:float
@dataclass
class Task:
 task_id:str; mission_id:str; description:str; authority:str; verifier:str; status:Decision|None=None; result:Any=None; evidence_ids:list[str]|None=None; attempts:int=0
 def __post_init__(self): self.evidence_ids=[] if self.evidence_ids is None else self.evidence_ids
@dataclass(frozen=True)
class Evidence: evidence_id:str; task_id:str; claim:str; value:Any; sufficient:bool; source:str; digest:str; state:EvidenceState
@dataclass(frozen=True)
class AuditEvent: event_id:str; timestamp:float; event:str; subject:str; data:dict; previous_digest:str|None; digest:str
class AuditLedger:
 def __init__(self): self.events=[]
 def append(self,event,subject,**data):
  prev=self.events[-1].digest if self.events else None; body={'event':event,'subject':subject,'data':data,'previous_digest':prev}; e=AuditEvent('evt-'+uuid4().hex,time.time(),event,subject,data,prev,digest(body)); self.events.append(e); return e
 def verify_chain(self):
  prev=None
  for e in self.events:
   if e.previous_digest!=prev or e.digest!=digest({'event':e.event,'subject':e.subject,'data':e.data,'previous_digest':prev}): return False
   prev=e.digest
  return True
 def export(self): return [asdict(e) for e in self.events]
class EvidenceLedger:
 def __init__(self): self.items={}
 def record(self,task_id,claim,value,sufficient,source,state=EvidenceState.REPORTED):
  eid='ev-'+uuid4().hex; self.items[eid]=Evidence(eid,task_id,claim,value,sufficient,source,digest(value),state); return eid
 def sufficient(self,ids): return bool(ids) and all(i in self.items and self.items[i].sufficient for i in ids)
class VerificationGate:
 def verify(self,task,evidence):
  if not evidence.sufficient(task.evidence_ids): return Decision.BLOCKED,'Evidence is missing or insufficient.'
  records=[evidence.items[i] for i in task.evidence_ids]
  passed=any(e.value is True or e.value=='PASS' for e in records)
  return (Decision.PASS,'Verified by sufficient evidence.') if passed else (Decision.FAIL,'Evidence does not establish success.')
class AMAOSEngine:
 def __init__(self): self.missions={}; self.tasks={}; self.agents={}; self.evidence=EvidenceLedger(); self.audit=AuditLedger(); self.verification=VerificationGate(); self.baseline={}
 def create_mission(self,goal,criteria,constraints,authorities,scope=''):
  if not goal.strip() or not criteria or not authorities: raise ValueError('goal, acceptance criteria and authority ceiling are required')
  mid='mission-'+uuid4().hex; self.missions[mid]=MissionContract(mid,goal,tuple(criteria),tuple(constraints),frozenset(authorities),scope,time.time()); self.audit.append('MISSION_CREATED',mid,goal=goal,scope=scope); return mid
 def register_agent(self,agent_or_id,authorities=None,execute=None):
  if authorities is None and execute is None and hasattr(agent_or_id,'agent_id'):
   agent_id=agent_or_id.agent_id; authorities=agent_or_id.authorities; execute=agent_or_id.execute
  else: agent_id=agent_or_id
  if not authorities or not callable(execute): raise ValueError('agent requires authority and callable execution')
  self.agents[agent_id]=(frozenset(authorities),execute); self.audit.append('AGENT_REGISTERED',agent_id,authorities=sorted(authorities))
 def add_task(self,mission_id,description,authority,verifier):
  m=self.missions[mission_id]
  if authority not in m.authorities: raise PermissionError('authority exceeds mission ceiling')
  tid='task-'+uuid4().hex; self.tasks[tid]=Task(tid,mission_id,description,authority,verifier); self.audit.append('TASK_CREATED',tid,mission_id=mission_id,authority=authority); return tid
 def execute(self,task_id,agent_id):
  t=self.tasks[task_id]; m=self.missions[t.mission_id]
  if not m.goal or not m.acceptance_criteria or t.authority not in m.authorities: return self._reject(t,'BOUNDARY_VIOLATION')
  if agent_id not in self.agents or t.authority not in self.agents[agent_id][0]: return self._reject(t,'AUTHORITY_DENIED')
  t.attempts+=1; self.audit.append('TASK_STARTED',task_id,agent_id=agent_id,attempt=t.attempts)
  try: t.result=self.agents[agent_id][1](t)
  except Exception as exc: t.status=Decision.FAIL; self.audit.append('EXECUTION_FAILED',task_id,error=type(exc).__name__); return t.status
  eid=self.evidence.record(task_id,'execution result',t.result,t.result is not None,'agent:'+agent_id,EvidenceState.REPRODUCIBLE); t.evidence_ids.append(eid); t.status,self_reason=self.verification.verify(t,self.evidence); self.audit.append('VERIFICATION',task_id,decision=t.status.value,reason=self_reason); return t.status
 def recover(self,task_id,agent_id):
  self.audit.append('RECOVERY_STARTED',task_id,previous=self.tasks[task_id].status.value if self.tasks[task_id].status else None); return self.execute(task_id,agent_id)
 def _reject(self,t,event): t.status=Decision.NO_GO; self.audit.append(event,t.task_id); return t.status
 def capture_regression_baseline(self): self.baseline={i:t.status for i,t in self.tasks.items() if t.status}; self.audit.append('REGRESSION_BASELINE_CAPTURED','system',count=len(self.baseline))
 def regression_check(self):
  for i,p in self.baseline.items():
   if self.tasks[i].status!=p and p==Decision.PASS: self.audit.append('REGRESSION_FAILED',i); return False,'Regression detected: '+i
  self.audit.append('REGRESSION_PASSED','system'); return True,'Regression gate passed.'
