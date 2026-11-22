import os
import json, urllib.request
BASE="http://127.0.0.1:8080/admin/api"
def api(m,p,tok=None,body=None):
    h={"Authorization":"Bearer "+tok} if tok else {}
    d=None
    if body is not None:
        d=json.dumps(body,ensure_ascii=False).encode(); h["Content-Type"]="application/json"
    r=urllib.request.Request(BASE+p,data=d,headers=h,method=m)
    with urllib.request.urlopen(r,timeout=60) as x: return json.loads(x.read().decode())
tok=api("POST","/user/login",body={"username":"admin","password":os.getenv("MAXKB_PASSWORD", "")})["data"]["token"]
a=api("GET","/workspace/default/application/01a1de97-cfe1-7f23-baa8-9caf5bdc25a8",tok)["data"]
print("应用:", a.get("name"))
print("模型:", a.get("model"))
print("知识库:", [k.get("name") for k in (a.get("knowledge_list") or [])])
print("工具:", a.get("tool_ids"))
print("技能:", a.get("skill_tool_ids"))
print("提示词含分流:", "第二类" in ((a.get("model_setting") or {}).get("system") or ""))