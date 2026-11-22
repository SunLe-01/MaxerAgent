# -*- coding: utf-8 -*-
import json, re
p=r"E:\Desktop\oncall-agent\output\chat_stream.txt"
raw=open(p,encoding="utf-8").read()
lines=[l[6:] for l in raw.splitlines() if l.startswith("data: ")]
ans=[]; nodes=set(); toolbits=[]
for l in lines:
    try: o=json.loads(l)
    except: continue
    nt=o.get("node_type"); nodes.add(nt)
    c=o.get("content") or ""
    if c:
        ans.append(c)
        if "tool" in c.lower() or "调用" in c: toolbits.append(c)
print("节点类型:", nodes)
print("回答长度:", sum(len(x) for x in ans))
print("="*60)
print("最终回答:\n", "".join(ans)[:1200])
print("="*60)
low=raw.lower()
for kw in ["tool_calls","mcp","tool-node","工具"]:
    print(f"包含 {kw!r}: {kw in low}")
idx=low.find("tool")
print("\n首次出现 tool 的上下文:\n", raw[max(0,idx-200):idx+400])