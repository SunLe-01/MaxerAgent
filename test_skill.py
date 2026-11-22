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
q="帮我审核一下这笔报销：10月8日到10日去杭州，P4 职级，住宿两晚共 1300，高铁二等座往返 600，市内交通 300，但我一直拖到 12 月 20 日才提交报销。有问题吗？"
body=json.dumps({"message":q,"stream":True,"re_chat":False},ensure_ascii=False).encode()
req=urllib.request.Request(f"{BASE}/chat_message/{cid}",data=body,headers={"Authorization":"Bearer "+tok,"Content-Type":"application/json"},method="POST")
buf=[]
with urllib.request.urlopen(req,timeout=300) as resp:
    for line in resp: buf.append(line.decode("utf-8","replace"))
raw="".join(buf)
open(r"E:\Desktop\oncall-agent\output\chat_skill.txt","w",encoding="utf-8").write(raw)
ans=[o.get("content") for o in (json.loads(l[6:]) for l in raw.splitlines() if l.startswith("data: ")) if o.get("content")]
text="".join(x for x in ans if x)
print("回答长度:",len(text))
tc=re.findall(r"<tool_calls_render>(.*?)</tool_calls_render>", text, re.S)
print("工具/技能调用次数:",len(tc))
for x in tc[:6]: print("  ",x[:150])
print("="*60)
print(re.sub(r"<tool_calls_render>.*?</tool_calls_render>","[调用]",text,flags=re.S)[:1400])