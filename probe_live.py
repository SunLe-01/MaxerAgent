# -*- coding: utf-8 -*-
"""Live end-to-end probe of the running MaxKB on 127.0.0.1:8080."""
import os
import io
import json
import sys
import urllib.error
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8080/admin/api"
WS = "default"
APP = "01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"


def api(method, path, token=None, body=None, base=BASE, timeout=120):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        return -1, repr(exc)


def main():
    status, body = api("POST", "/user/login", body={"username": "admin", "password": os.getenv("MAXKB_PASSWORD", "")})
    print("login:", status, body[:120])
    if status != 200:
        return
    tok = json.loads(body)["data"]["token"]

    status, body = api("GET", f"/workspace/{WS}/application/{APP}", tok)
    app = json.loads(body)["data"]
    print("app:", app.get("name"), "| is_publish:", app.get("is_publish"), "| type:", app.get("type"))
    print("  model:", (app.get("model") or {}).get("name") if isinstance(app.get("model"), dict) else app.get("model_id"))
    print("  knowledge_list:", [k.get("name") for k in (app.get("knowledge_list") or [])])
    print("  tool_ids:", app.get("tool_ids"), "| skill_tool_ids:", app.get("skill_tool_ids"))
    print("  knowledge_setting:", json.dumps(app.get("knowledge_setting"), ensure_ascii=False))

    status, body = api("GET", f"/workspace/{WS}/tool", tok)
    print("\nworkspace tool list:", status, body[:300])

    status, body = api("GET", f"/workspace/{WS}/application/{APP}/open", tok)
    print("\nopen:", status, body[:200])
    data = json.loads(body).get("data") or {}
    cid = data if isinstance(data, str) else data.get("chat_id")
    print("chat_id:", cid)
    if not cid:
        return

    questions = [
        "二类城市 P4 员工的住宿上限是多少？",
        "我下周去成都出差 2 晚，住宿每晚 650 块，P4 职级，一共出差 3 天，能报多少？",
        "帮我审核一下这笔报销：10月1日到10日去杭州，P4 职级，住宿两晚共1300，高铁二等座往返1600，市内交通300，但我一直拖到12月20日才提交报销。有问题吗？",
    ]
    for q in questions:
        print("\n" + "=" * 70)
        print("Q:", q)
        payload = json.dumps({"message": q, "stream": True, "re_chat": False}, ensure_ascii=False).encode()
        req = urllib.request.Request(
            f"{BASE}/chat_message/{cid}", data=payload,
            headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"}, method="POST",
        )
        buf = []
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                for line in resp:
                    buf.append(line.decode("utf-8", "replace"))
        except Exception as exc:  # noqa: BLE001
            print("STREAM ERROR:", repr(exc))
        raw = "".join(buf)
        text = []
        tools = []
        for line in raw.splitlines():
            if not line.startswith("data: "):
                continue
            try:
                obj = json.loads(line[6:])
            except Exception:  # noqa: BLE001
                continue
            c = obj.get("content") or ""
            if c:
                text.append(c)
                if "<tool_calls_render>" in c:
                    tools.append(c)
        answer = "".join(text)
        print(f"  answer_len={len(answer)} frames={len(raw.splitlines())} tool_render={len(tools)}")
        print("  answer:", answer.replace("\n", " ")[:600])


if __name__ == "__main__":
    main()
