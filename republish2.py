# -*- coding: utf-8 -*-
import os
import json, urllib.request, urllib.error
BASE="http://127.0.0.1:8080/admin/api"; WS="default"; APP="01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"
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
r=api("PUT",f"/workspace/{WS}/application/{APP}/publish",tok,{})
print("发布:", r.get("code"), r.get("message"))