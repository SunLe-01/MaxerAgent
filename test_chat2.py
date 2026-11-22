# -*- coding: utf-8 -*-
import os
import json, urllib.request, urllib.error
BASE="http://127.0.0.1:8080/admin/api"
WS="default"; APP="01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"
def api(m,p,tok=None,body=None):
    h={"Authorization":"Bearer "+tok} if tok else {}
    d=None
    if body is not None:
        d=json.dumps(body,ensure_ascii=False).encode(); h["Content-Type"]="application/json"
    r=urllib.request.Request(BASE+p,data=d,headers=h,method=m)
    try:
        with urllib.request.urlopen(r,timeout=240) as x: return json.loads(x.read().decode())
    except urllib.error.HTTPError as e: return {"code":e.code,"message":e.read().decode()[:300]}
tok=api("POST","/user/login",body={"username":"admin","password":os.getenv("MAXKB_PASSWORD", "")})["data"]["token"]
op=api("GET",f"/workspace/{WS}/application/{APP}/open",tok)
cid=op.get("data") or {}
cid=cid if isinstance(cid,str) else cid.get("chat_id")
print("chat_id:",cid)
q="我下周去成都出差 2 晚，住宿每晚 650 块，P4 职级，一共出差 3 天，能报多少？"
body=json.dumps({"message":q},ensure_ascii=False).encode()
req=urllib.request.Request(f"{BASE}/chat_message/{cid}",data=body,headers={"Authorization":"Bearer "+tok,"Content-Type":"application/json"},method="POST")
try:
    buf=[]
    with urllib.request.urlopen(req,timeout=300) as resp:
        for line in resp: buf.append(line.decode("utf-8","replace"))
    out="".join(buf)
    open(r"E:\Desktop\oncall-agent\output\chat_stream.txt","w",encoding="utf-8").write(out)
    print("流长度:",len(out))
    print("出现 tool/mcp 字样:", ("tool" in out.lower()) or ("mcp" in out.lower()))
    print(out[:2000])
except urllib.error.HTTPError as e:
    print("HTTP",e.code,e.read().decode()[:300])