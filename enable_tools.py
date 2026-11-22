# -*- coding: utf-8 -*-
import os
import json, urllib.request, urllib.error
BASE="http://127.0.0.1:8080/admin/api"; WS="default"
TOOL="01a1ded0-6d64-7eb1-a63d-6367d38f8fcf"
SKILL="01a1ded0-bc5b-7953-a34f-b0fd200e88fb"
def api(m,p,tok=None,body=None):
    h={"Authorization":"Bearer "+tok} if tok else {}
    d=None
    if body is not None:
        d=json.dumps(body,ensure_ascii=False).encode(); h["Content-Type"]="application/json"
    r=urllib.request.Request(BASE+p,data=d,headers=h,method=m)
    try:
        with urllib.request.urlopen(r,timeout=120) as x: return json.loads(x.read().decode())
    except urllib.error.HTTPError as e: return {"code":e.code,"message":e.read().decode()[:300]}
tok=api("POST","/user/login",body={"username":"admin","password":os.getenv("MAXKB_PASSWORD", "")})["data"]["token"]
for tid in (TOOL, SKILL):
    t=api("GET",f"/workspace/{WS}/tool/{tid}",tok)["data"]
    payload={k:t.get(k) for k in ("name","desc","tool_type","code","input_field_list","init_field_list","scope")}
    payload["is_active"]=True
    r=api("PUT",f"/workspace/{WS}/tool/{tid}",tok,payload)
    t2=api("GET",f"/workspace/{WS}/tool/{tid}",tok)["data"]
    print(f"{t2.get('name')}: 更新={r.get('message')} is_active={t2.get('is_active')}")