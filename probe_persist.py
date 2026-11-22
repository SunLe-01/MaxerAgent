# -*- coding: utf-8 -*-
"""单条对话后立即查库，定位"对话没落库"的原因。"""
import os
import io
import json
import sys
import time
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8080/admin/api"
WS = "default"
APP = "01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"


def api(method, path, token=None, body=None, timeout=120):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


tok = json.loads(api("POST", "/user/login", body={"username": "admin", "password": os.getenv("MAXKB_PASSWORD", "")}))["data"]["token"]

# 用 debug 参数（管理端调试对话通常带 dataset_id / debug=True）
op = json.loads(api("GET", f"/workspace/{WS}/application/{APP}/open", tok))
print("open resp:", json.dumps(op, ensure_ascii=False)[:200])
cid = op.get("data") if isinstance(op.get("data"), str) else (op.get("data") or {}).get("chat_id")
print("chat_id:", cid)

payload = json.dumps({"message": "二类城市 P4 的住宿上限是多少？", "stream": True, "re_chat": False}, ensure_ascii=False).encode()
req = urllib.request.Request(
    f"{BASE}/chat_message/{cid}", data=payload,
    headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"}, method="POST",
)
buf = []
with urllib.request.urlopen(req, timeout=120) as resp:
    for line in resp:
        buf.append(line.decode("utf-8", "replace"))
print("frames:", len(buf))

# 最后几帧看看有没有错误/是否给了 chat_record_id
tail = [l for l in buf[-6:] if l.startswith("data: ")]
for l in tail[-2:]:
    try:
        o = json.loads(l[6:])
        print("last frame keys:", {k: (str(v)[:80]) for k, v in o.items()})
    except Exception:
        print("raw:", l[:200])

time.sleep(2)
print("chat_id used:", cid)
