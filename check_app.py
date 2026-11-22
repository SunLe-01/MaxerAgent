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
a=api("GET",f"/workspace/{WS}/application/{APP}",tok)["data"]
print("应用 tool_ids      :", a.get("tool_ids"))
print("应用 skill_tool_ids:", a.get("skill_tool_ids"))
print("应用 mcp_tool_ids  :", a.get("mcp_tool_ids"))
print("应用 model_setting.system 前 80 字:", (a.get("model_setting") or {}).get("system","")[:80].replace("\n"," "))
print("知识库检索参数:", a.get("knowledge_setting"))