# -*- coding: utf-8 -*-
import os
import json, urllib.request
BASE="http://127.0.0.1:8080/admin/api"; WS="default"; APP="01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"
def api(m,p,tok=None,body=None):
    h={}
    if tok: h["Authorization"]="Bearer "+tok
    d=None
    if body is not None:
        d=json.dumps(body,ensure_ascii=False).encode(); h["Content-Type"]="application/json"
    r=urllib.request.Request(BASE+p,data=d,headers=h,method=m)
    with urllib.request.urlopen(r,timeout=60) as x: return json.loads(x.read().decode())
tok=api("POST","/user/login",body={"username":"admin","password":os.getenv("MAXKB_PASSWORD", "")})["data"]["token"]
chats=api("GET",f"/workspace/{WS}/application/{APP}/chat/1/5",tok)["data"]
recs=chats.get("records") or []
print("会话数:", len(recs))
if recs:
    cid=recs[0]["id"]
    rr=api("GET",f"/workspace/{WS}/application/{APP}/chat/{cid}/chat_record/1/10",tok)["data"]
    rows=rr.get("records") or []
    print("记录数:", len(rows))
    for r in rows[:4]:
        q=(r.get("problem_text") or "")[:40]
        d=r.get("details") or {}
        keys=list(d.keys()) if isinstance(d,dict) else type(d).__name__
        print("-"*50)
        print("问题:", q)
        print("details 顶层键:", keys)
        if isinstance(d,dict):
            for k in ("step_details","steps","tool","mcp","search"):
                if k in d:
                    v=d[k]
                    print(f"  {k}:", json.dumps(v,ensure_ascii=False)[:300])
        print("引用分段数:", len(r.get("knowledge_list") or []))