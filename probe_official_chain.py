# -*- coding: utf-8 -*-
"""走「正式对话」链路（非 debug），采集会落库的指标。"""
import os
import io
import json
import sys
import time
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ADMIN = "http://127.0.0.1:8080/admin/api"
CHAT = "http://127.0.0.1:8080/chat/api"
WS = "default"
APP = "01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"
TOKEN = "e6d27c065fef2cca"  # application_access_token


def post(url, payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=json.dumps(payload, ensure_ascii=False).encode(),
                                 headers=headers, method="POST")
    return urllib.request.urlopen(req, timeout=300)


def main():
    tok = json.loads(urllib.request.urlopen(
        urllib.request.Request(ADMIN + "/user/login",
                               data=json.dumps({"username": "admin", "password": os.getenv("MAXKB_PASSWORD", "")}).encode(),
                               headers={"Content-Type": "application/json"}, method="POST"),
        timeout=60).read().decode())["data"]["token"]

    # 管理端 open（debug=True）
    op = json.loads(urllib.request.urlopen(
        urllib.request.Request(f"{ADMIN}/workspace/{WS}/application/{APP}/open",
                               headers={"Authorization": "Bearer " + tok}), timeout=60
    ).read().decode())["data"]

    # 正式链路：先 POST /chat/api/auth/anonymous 换匿名 token，再 GET /chat/api/open（debug=False）
    try:
        r = post(f"{CHAT}/auth/anonymous", {"access_token": TOKEN})
        auth = json.loads(r.read().decode())
        anon = auth.get("data")
        print("auth/anonymous ->", json.dumps(auth, ensure_ascii=False)[:160])
    except Exception as exc:
        print("auth/anonymous 失败:", exc)
        return

    def open_chat():
        req = urllib.request.Request(f"{CHAT}/open", headers={"Authorization": "Bearer " + anon})
        d = json.loads(urllib.request.urlopen(req, timeout=60).read().decode()).get("data") or {}
        return d.get("chat_id") if isinstance(d, dict) else d
    qs = [
        ("查规定", "二类城市 P4 员工的住宿上限是多少？"),
        ("算金额", "我下周去成都出差 2 晚，住宿每晚 650 块，P4 职级，一共出差 3 天，能报多少？"),
        ("审单据", "帮我审核一下这笔报销：10月1日到10日去杭州，P4 职级，住宿两晚共1300，高铁二等座往返1600，市内交通300，但我一直拖到12月20日才提交报销。有问题吗？"),
    ]

    cid = None
    for kind, question in qs:
        if cid is None:
            cid = open_chat()
            print("正式会话 chat_id:", cid)

        t0 = time.time()
        first = None
        buf = []
        req = urllib.request.Request(
            f"{CHAT}/chat_message/{cid}",
            data=json.dumps({"message": question, "stream": True, "re_chat": False}, ensure_ascii=False).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + anon}, method="POST")
        with urllib.request.urlopen(req, timeout=300) as resp:
            for line in resp:
                if first is None:
                    first = time.time() - t0
                buf.append(line.decode("utf-8", "replace"))
        total = time.time() - t0

        text, tools = [], []
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
                    tools.append(c)
        ans = "".join(text)
        print("=" * 70)
        print(f"[{kind}] 首字 {first:.2f}s 总 {total:.2f}s 工具 {len(tools)} 次 长度 {len(ans)}")
        print("  答:", ans.replace(chr(10), " ")[:200])


if __name__ == "__main__":
    main()
