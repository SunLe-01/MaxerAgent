# -*- coding: utf-8 -*-
"""启动后验证：走公开链路（会落库），跑两个问题确认工具与知识库都正常。"""
import os
import io
import json
import sys
import time
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ADMIN = "http://127.0.0.1:18080/admin/api"
CHAT = "http://127.0.0.1:18080/chat/api"
WS = "default"
APP_NAME = "差旅工作流实验"


def post(url, payload, token=None, timeout=300):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(
        url, data=json.dumps(payload, ensure_ascii=False).encode(),
        headers=headers, method="POST")
    return urllib.request.urlopen(req, timeout=timeout)


def main():
    login = json.loads(urllib.request.urlopen(urllib.request.Request(
        ADMIN + "/user/login",
        data=json.dumps({"username": "admin", "password": os.getenv("MAXKB_PASSWORD", "")}).encode(),
        headers={"Content-Type": "application/json"}, method="POST"), timeout=60
    ).read().decode())
    tok = login["data"]["token"]

    page = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"{ADMIN}/workspace/{WS}/application/1/50",
        headers={"Authorization": "Bearer " + tok}), timeout=60).read().decode())
    app = next(a for a in page["data"]["records"] if a["name"] == APP_NAME)
    print("应用:", app["name"], "| 已发布:", app["is_publish"])

    at = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"{ADMIN}/workspace/{WS}/application/{app['id']}/access_token",
        headers={"Authorization": "Bearer " + tok}), timeout=60).read().decode())
    access_token = at["data"]["access_token"]

    anon = json.loads(post(f"{CHAT}/auth/anonymous", {"access_token": access_token}).read().decode())["data"]
    cid = json.loads(urllib.request.urlopen(urllib.request.Request(
        f"{CHAT}/open", headers={"Authorization": "Bearer " + anon}), timeout=60
    ).read().decode())["data"]
    cid = cid.get("chat_id") if isinstance(cid, dict) else cid

    for q in ["成都 2 晚 650，P4，3 天能报多少？", "二类城市 P4 员工的住宿上限是多少？"]:
        t0 = time.time()
        buf = []
        req = urllib.request.Request(
            f"{CHAT}/chat_message/{cid}",
            data=json.dumps({"message": q, "stream": True, "re_chat": False}, ensure_ascii=False).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + anon}, method="POST")
        with urllib.request.urlopen(req, timeout=300) as resp:
            for line in resp:
                buf.append(line.decode("utf-8", "replace"))
        total = time.time() - t0

        text, tools = [], 0
        for line in buf:
            if not line.startswith("data: "):
                continue
            try:
                o = json.loads(line[6:])
            except Exception:
                continue
            c = o.get("content") or ""
            if c:
                text.append(c)
                if "<tool_calls_render>" in c:
                    tools += 1
        ans = "".join(text)
        flag = "OK" if ("异常" not in ans and "Exception" not in ans and ans.strip()) else "FAIL"
        print("=" * 68)
        print(f"[{flag}] {q}")
        print(f"  耗时 {total:.1f}s | 工具调用 {tools} 次")
        print(f"  {ans.replace(chr(10), ' ')[:220]}")


if __name__ == "__main__":
    main()
