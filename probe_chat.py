# -*- coding: utf-8 -*-
import os
import json, urllib.request, urllib.error
BASE="http://127.0.0.1:8080/admin/api"; WS="default"; APP="01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"
def raw(m,p,tok=None):
    h={"Authorization":"Bearer "+tok} if tok else {}
    r=urllib.request.Request(BASE+p,headers=h,method=m)
    try:
        with urllib.request.urlopen(r,timeout=60) as x: return x.status, x.read().decode()
    except urllib.error.HTTPError as e: return e.code, e.read().decode()[:300]
tok=json.loads(raw("POST","/user/login")[1] if False else "{}") if False else None
import urllib.request as u
req=u.Request(BASE+"/user/login",data=json.dumps({"username":"admin","password":os.getenv("MAXKB_PASSWORD", "")}).encode(),headers={"Content-Type":"application/json"},method="POST")
tok=json.loads(u.urlopen(req).read())["data"]["token"]
for p in [f"/workspace/{WS}/application/{APP}/chat/1/5", f"/workspace/{WS}/application/{APP}/chat"]:
    s,b=raw("GET",p,tok)
    print(p,"->",s,b[:200])