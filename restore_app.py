# -*- coding: utf-8 -*-
import os
import json, urllib.request, urllib.error
BASE="http://127.0.0.1:8080/admin/api"
WS="default"; APP="01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"
MODEL="01a1de8f-98fe-71a2-998a-df86ea6e0e00"   # DeepSeek-Flash
KB="01a1de96-b743-7db3-a17a-724eb13b64d5"      # 测试知识库
def api(m,p,tok=None,body=None):
    h={"Authorization":"Bearer "+tok} if tok else {}
    d=None
    if body is not None:
        d=json.dumps(body,ensure_ascii=False).encode(); h["Content-Type"]="application/json"
    r=urllib.request.Request(BASE+p,data=d,headers=h,method=m)
    try:
        with urllib.request.urlopen(r,timeout=240) as x: return json.loads(x.read().decode())
    except urllib.error.HTTPError as e: return {"code":e.code,"message":e.read().decode()[:400]}
tok=api("POST","/user/login",body={"username":"admin","password":os.getenv("MAXKB_PASSWORD", "")})["data"]["token"]
a=api("GET",f"/workspace/{WS}/application/{APP}",tok)["data"]
print("当前 model:",a.get("model"),"| 知识库:",[k.get("name") for k in (a.get("knowledge_list") or [])])
ms=a.get("model_setting") or {}
payload={"name":a.get("name"),"desc":a.get("desc"),"model_id":MODEL,
         "knowledge_id_list":[KB],"model_setting":ms,
         "tool_ids":a.get("tool_ids"),"skill_tool_ids":a.get("skill_tool_ids")}
r=api("PUT",f"/workspace/{WS}/application/{APP}",tok,payload)
print("更新:",r.get("code"),r.get("message"))
a2=api("GET",f"/workspace/{WS}/application/{APP}",tok)["data"]
print("恢复后 model:",a2.get("model"))
print("知识库:",[k.get("name") for k in (a2.get("knowledge_list") or [])])
print("工具:",a2.get("tool_ids"),"技能:",a2.get("skill_tool_ids"))
print("提示词含第二类:", "第二类" in ((a2.get("model_setting") or {}).get("system") or ""))