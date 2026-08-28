import pytest
from am_aos.runtime import AMAOSEngine,Decision

def make():
 e=AMAOSEngine(); m=e.create_mission('g',['c'],['immutable'],['execute'],'test'); return e,m

def test_happy_path_and_audit():
 e,m=make(); e.register_agent('a',{'execute'},lambda t:True); t=e.add_task(m,'x','execute','v'); assert e.execute(t,'a')==Decision.PASS; e.capture_regression_baseline(); assert e.regression_check(); assert e.audit.verify_chain()

def test_authority_is_hard_boundary():
 e,m=make(); e.register_agent('a',{'read'},lambda t:True); t=e.add_task(m,'x','execute','v'); assert e.execute(t,'a')==Decision.NO_GO

def test_failure_is_not_pass():
 e,m=make(); e.register_agent('a',{'execute'},lambda t:False); t=e.add_task(m,'x','execute','v'); assert e.execute(t,'a')==Decision.FAIL

def test_regression_blocks():
 e,m=make(); e.register_agent('a',{'execute'},lambda t:True); t=e.add_task(m,'x','execute','v'); assert e.execute(t,'a')==Decision.PASS; e.capture_regression_baseline(); e.tasks[t].status=Decision.FAIL; assert not e.regression_check()

def test_missing_contract_rejected():
 e=AMAOSEngine();
 with pytest.raises(ValueError): e.create_mission('',[],[],[])
