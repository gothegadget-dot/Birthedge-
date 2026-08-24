#!/usr/bin/env python3
import os, time, json, urllib.request, fcntl
from concurrent.futures import ThreadPoolExecutor, as_completed
BASE="/data/data/com.termux/files/home/BIRTH_EDGE"
LOG=os.path.join(BASE,"data/event_log.jsonl")
def fetch(offset):
    url=f"https://frontend-api-v3.pump.fun/coins?offset={offset}&limit=30&sort=created_timestamp&order=DESC"
    req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data=json.loads(r.read().decode())
            evs=[]
            for c in data:
                mcap=int(float(c.get("usd_market_cap",0))*100)
                if c.get("mint") and mcap>=1000:
                    evs.append({"type":"birth_seen","symbol":str(c.get("symbol",""))[:20],"mint":c.get("mint"),"mcap_cents":mcap,"t":int(time.time())})
            return evs
    except Exception as e:
        print(f"[ERR] {offset} {e}", flush=True); return []
print("[BOOT] BIRTH_EDGE 10-node", flush=True)
seen=set()
try:
 for l in open(LOG): seen.add(json.loads(l).get("mint"))
except: pass
while True:
 s=time.time()
 offs=[0,30,60,90,120,150,180,210,240,270]
 all_ev=[]
 with ThreadPoolExecutor(max_workers=10) as ex:
  futs=[ex.submit(fetch,o) for o in offs]
  for f in as_completed(futs): all_ev.extend(f.result())
 new=0
 for ev in all_ev:
  if ev["mint"] not in seen:
   seen.add(ev["mint"]); new+=1
   try:
    with open(LOG,"a") as fh:
     fcntl.flock(fh,fcntl.LOCK_EX); fh.write(json.dumps(ev,sort_keys=True)+"\n"); fcntl.flock(fh,fcntl.LOCK_UN)
   except: pass
 print(f"[EXEC] {time.time()-s:.2f}s | {new} new | {len(seen)} mints | 10 opens", flush=True)
 time.sleep(5)
