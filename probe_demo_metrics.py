# -*- coding: utf-8 -*-
"""面试演示用的真实指标采集：首字时延、总时延、工具调用轨迹。"""
import os
import io
import json
import sys
import time
import urllib.error
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


def main():
    tok = json.loads(api("POST", "/user/login", body={"username": "admin", "password": os.getenv("MAXKB_PASSWORD", "")}))["data"]["token"]
    data = json.loads(api("GET", f"/workspace/{WS}/application/{APP}/open", tok)).get("data") or {}
    cid = data if isinstance(data, str) else data.get("chat_id")

    questions = [
        ("查规定", "二类城市 P4 员工的住宿上限是多少？"),
        ("算金额", "我下周去成都出差 2 晚，住宿每晚 650 块，P4 职级，一共出差 3 天，能报多少？"),
        ("审单据", "帮我审核一下这笔报销：10月1日到10日去杭州，P4 职级，住宿两晚共1300，高铁二等座往返1600，市内交通300，但我一直拖到12月20日才提交报销。有问题吗？"),
    ]

    for kind, q in questions:
        payload = json.dumps({"message": q, "stream": True, "re_chat": False}, ensure_ascii=False).encode()
        req = urllib.request.Request(
            f"{BASE}/chat_message/{cid}", data=payload,
            headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"}, method="POST",
        )
        t0 = time.time()
        first_chunk = None
        buf = []
        with urllib.request.urlopen(req, timeout=300) as resp:
            for line in resp:
                if first_chunk is None:
                    first_chunk = time.time() - t0
                buf.append(line.decode("utf-8", "replace"))
        total = time.time() - t0
        raw = "".join(buf)

        text, tools = [], []
        for line in raw.splitlines():
            if not line.startswith("data: "):
                continue
            try:
                obj = json.loads(line[6:])
            except Exception:
                continue
            c = obj.get("content") or ""
            if c:
                text.append(c)
                if "<tool_calls_render>" in c:
                    tools.append(c)
        ans = "".join(text)

        names = []
        for t in tools:
            for seg in t.split("<tool_calls_render>"):
                seg = seg.strip()
                if not seg:
                    continue
                try:
                    names.append(json.loads(seg.rstrip("</tool_calls_render>")).get("title"))
                except Exception:
                    pass

        print("=" * 72)
        print(f"[{kind}] {q[:40]}")
        print(f"  首字时延 {first_chunk:.2f}s | 总时延 {total:.2f}s | 工具调用 {len(tools)} 次 | 调用名 {names}")
        print(f"  回答长度 {len(ans)} 字")
        print(f"  答案: {ans.replace(chr(10), ' ')[:300]}")


if __name__ == "__main__":
    main()
