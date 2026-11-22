# -*- coding: utf-8 -*-
import os
import json, re, urllib.request
BASE="http://127.0.0.1:8080/admin/api"; WS="default"; APP="01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"
def api(m,p,tok=None,body=None):
    h={"Authorization":"Bearer "+tok} if tok else {}
    d=None
    if body is not None:
        d=json.dumps(body,ensure_ascii=False).encode(); h["Content-Type"]="application/json"
    r=urllib.request.Request(BASE+p,data=d,headers=h,method=m)
    with urllib.request.urlopen(r,timeout=240) as x: return json.loads(x.read().decode())
tok=api("POST","/user/login",body={"username":"admin","password":os.getenv("MAXKB_PASSWORD", "")})["data"]["token"]
d=api("GET",f"/workspace/{WS}/application/{APP}/open",tok).get("data")
cid=d if isinstance(d,str) else (d or {}).get("chat_id")
print("chat_id:",cid)
q="我下周去成都出差 2 晚，住宿每晚 650 块，P4 职级，一共出差 3 天，能报多少？"
body=json.dumps({"message":q,"stream":True,"re_chat":False},ensure_ascii=False).encode()
req=urllib.request.Request(f"{BASE}/chat_message/{cid}",data=body,headers={"Authorization":"Bearer "+tok,"Content-Type":"application/json"},method="POST")
buf=[]
with urllib.request.urlopen(req,timeout=300) as resp:
    for line in resp: buf.append(line.decode("utf-8","replace"))
raw="".join(buf)
open(r"E:\Desktop\oncall-agent\output\chat_stream2.txt","w",encoding="utf-8").write(raw)
ans=[o.get("content") for o in (json.loads(l[6:]) for l in raw.splitlines() if l.startswith("data: ")) if o.get("content")]
text="".join(x for x in ans if x)
print("回答长度:",len(text))
tc=re.findall(r"<tool_calls_render>(.*?)</tool_calls_render>", text, re.S)
print("工具调用次数:",len(tc))
for x in tc[:5]: print("  调用:",x[:200].encode("utf-8","replace").decode("utf-8"))
print("="*60)
print(re.sub(r"<tool_calls_render>.*?</tool_calls_render>","[工具调用]",text,flags=re.S)[:1500])