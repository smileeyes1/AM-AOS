import argparse
from .runtime import AMAOSEngine

def main():
 p=argparse.ArgumentParser(prog='am-aos'); p.add_argument('--self-check',action='store_true'); a=p.parse_args()
 if a.self_check:
  e=AMAOSEngine(); m=e.create_mission('self-check',['execution succeeds'],['constitutional-boundary'],['execute'],'local'); e.register_agent('self',{'execute'},lambda task: True); t=e.add_task(m,'self check','execute','local-verifier'); assert e.execute(t,'self').value=='PASS'; e.capture_regression_baseline(); assert e.regression_check(); assert e.audit.verify_chain(); print('SELF-CHECK PASS')
if __name__=='__main__': main()
