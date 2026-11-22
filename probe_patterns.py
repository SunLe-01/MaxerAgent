# -*- coding: utf-8 -*-
"""实测：SIMPLE 应用（走 create_deep_agent）是否会自发使用 write_todos / task 工具。

import os
用于验证 Plan-and-Execute 是否真的在运行，而不只是"工具存在"。
"""
import io
import json
import sys
import time
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ADMIN = "http://127.0.0.1:8080/admin/api"
CHAT = "http://127.0.0.1:8080/chat/api"
WS = "default"
APP_SIMPLE = "01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"  # 差旅制度答疑（测试）


def main():
    tok = json.loads(urllib.request.urlopen(urllib.request.Request(
        ADMIN + "/user/login",
        data=json.dumps({"username": "admin", "password": os.getenv("MAXKB_PASSWORD", "")}).encode(),
        headers={"Content-Type": "application/json"}, method="POST"), timeout=60
    ).read().decode())["data"]["token"]

    at = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"{ADMIN}/workspace/{WS}/application/{APP_SIMPLE}/access_token",
        headers={"Authorization": "Bearer " + tok}), timeout=60).read().decode())["data"]
    access_token = at["access_token"]

    anon = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"{CHAT}/auth/anonymous",
        data=json.dumps({"access_token": access_token}).encode(),
        headers={"Content-Type": "application/json"}, method="POST"), timeout=60
    ).read().decode())["data"]

    cid = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"{CHAT}/open", headers={"Authorization": "Bearer " + anon}), timeout=60
    ).read().decode())["data"]
    cid = cid.get("chat_id") if isinstance(cid, dict) else cid

    # 需要多步的问题：先查标准、再算钱、再提示超标
    q = "我在成都出差 2 晚，每晚 650，P4 职级，请你先查一下住宿标准，再算我能报多少，最后告诉我超标了怎么办。"

    req = urllib.request.Request(
        f"{CHAT}/chat_message/{cid}",
        data=json.dumps({"message": q, "stream": True, "re_chat": False}, ensure_ascii=False).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + anon}, method="POST")

    t0 = time.time()
    buf = []
    with urllib.request.urlopen(req, timeout=300) as resp:
        for line in resp:
            buf.append(line.decode("utf-8", "replace"))
    print(f"耗时 {time.time()-t0:.1f}s")

    raw = "".join(buf)
    tools_used = []
    for line in raw.splitlines():
        if not line.startswith("data: "):
            continue
        try:
            o = json.loads(line[6:])
        except Exception:
            continue
        c = o.get("content") or ""
        if "<tool_calls_render>" in c:
            for seg in c.split("<tool_calls_render>"):
                seg = seg.strip().rstrip("</tool_calls_render>")
                if not seg:
                    continue
                try:
                    tools_used.append(json.loads(seg).get("title"))
                except Exception:
                    pass

    print("\n=== 工具调用序列 ===")
    for i, t in enumerate(tools_used, 1):
        print(f"  {i}. {t}")

    print("\n=== 是否出现 Plan-and-Execute 迹象 ===")
    for kw in ["write_todos", "todos", "task", "general-purpose"]:
        print(f"  {kw:20} -> {kw in raw}")

    ans = []
    for line in raw.splitlines():
        if not line.startswith("data: "):
            continue
        try:
            o = json.loads(line[6:])
        except Exception:
            continue
        c = o.get("content") or ""
        if c and "<tool_calls_render>" not in c:
            ans.append(c)
    print("\n=== 最终回答（前 400 字）===")
    print("".join(ans)[:400])


if __name__ == "__main__":
    main()
