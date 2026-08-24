import json, fcntl, time, os, hashlib
BASE="/data/data/com.termux/files/home/BIRTH_EDGE"
LOG=os.path.join(BASE,"data/event_log.jsonl")
TREAS=os.path.join(BASE,"data/treasury.jsonl")
def load():
 s={}
 try:
  for l in open(LOG):
   try:
    ev=json.loads(l)
    if ev.get("symbol") and ev.get("mcap_cents",0)>500: s[ev["symbol"]]=ev
   except: pass
 except: pass
 return s
def opens():
 o={}
 try:
  for l in open(TREAS):
   try:
    ev=json.loads(l); sym=ev.get("symbol")
    if not sym: continue
    if ev["type"]=="trade_open": o[sym]=ev
    if ev["type"] in ("profit","loss"): o.pop(sym,None)
   except: pass
 except: pass
 return o
def close(sym,entry,now,amt):
 ratio=now/max(1,entry)
 if ratio<0.001 or ratio>1000: return
 pnl=amt*(ratio-1)
 pnl=max(-1.0,min(1.0,pnl))
 side="profit" if pnl>0 else "loss"
 ev={"type":side,"t":int(time.time()),"symbol":sym,"mcap_cents":now,"entry_mcap":entry,"exit_mcap":now,"amount_sol":abs(pnl),"side":side,"proof":hashlib.sha256(f"{sym}{now}{time.time()}".encode()).hexdigest()[:8]}
 for p in [TREAS,LOG]:
  try:
   with open(p,"a") as f:
    fcntl.flock(f,fcntl.LOCK_EX); f.write(json.dumps(ev,sort_keys=True)+"\n"); fcntl.flock(f,fcntl.LOCK_UN)
  except: pass
 print(f"[EXIT] {side} {sym} {entry}->{now} P/L {pnl:.4f}",flush=True)
def run():
 st=load(); op=opens()
 print(f"[EXIT_LOOP] {len(op)} open {len(st)} mints",flush=True)
 closed=0
 for sym,pos in list(op.items()):
  cur=st.get(sym)
  if not cur: continue
  e=pos["mcap_cents"]; n=cur["mcap_cents"]
  if n>=e*2:
   close(sym,e,n,pos.get("amount_sol",0.01)*2); closed+=1
  elif n<=e*0.5:
   close(sym,e,n,pos.get("amount_sol",0.01)); closed+=1
 if closed==0:
  print(f"[EXIT_LOOP] no exits - ratios not hit",flush=True)
if __name__=="__main__": run()
