# -*- coding: utf-8 -*-
"""修正系统提示词，并实跑一次对话验证工具是否被调用"""
import os
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8080/admin/api"
CHAT = "http://127.0.0.1:8080/chat/api"
WS = "default"
APP = "01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"

SYSTEM_PROMPT = """你是星澜信息技术有限公司的「差旅与费用报销制度」助手。你具备两种能力，请按问题类型自动选择。

【第一类：查规定 → 用知识库】
当用户问"标准是多少""规定是什么""能不能报销""第几条"时，只依据【参考资料】回答，并标注依据条款。

【第二类：算金额 / 审单据 → 用工具】
- 用户问"我这次出差能报多少""住宿超标多少""能拿多少补贴"这类需要计算的 → 必须调用「差旅报销试算器」，不要自己心算。
- 用户贴出报销明细并要求"审核""看看有没有问题" → 必须使用「差旅报销单审核」技能。

【第三类：两者都不适用 → 明确说不知道】
只有前两类都不成立时，才回复：知识库中未找到相关条款，建议咨询行政人事部。

补充规则：
1. 计算结果必须来自工具返回值，禁止自行推算金额。
2. 引用结果时说明依据，例如"按第十条住宿标准表"。
3. 金额保留两位小数，使用简体中文。
4. 缺少职级、城市、天数等必要信息时，先追问再计算。"""


def api(method, path, token=None, body=None, base=BASE):
    headers = {}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"code": e.code, "message": e.read().decode("utf-8", "replace")[:500]}


def stream_chat(token, chat_id, message):
    url = "%s/chat_message/%s" % (CHAT, chat_id)
    body = json.dumps({"message": message}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        method="POST")
    chunks = []
    with urllib.request.urlopen(req, timeout=300) as resp:
        for line in resp:
            chunks.append(line.decode("utf-8", "replace"))
    return "".join(chunks)


if __name__ == "__main__":
    tok = api("POST", "/user/login", body={"username": "admin", "password": os.getenv("MAXKB_PASSWORD", "")})["data"]["token"]
    print("1) 登录 OK")

    app = api("GET", "/workspace/%s/application/%s" % (WS, APP), tok)["data"]
    ms = app.get("model_setting") or {}
    ms["system"] = SYSTEM_PROMPT
    payload = {"name": app.get("name"), "desc": app.get("desc"), "model_setting": ms}
    r = api("PUT", "/workspace/%s/application/%s" % (WS, APP), tok, payload)
    print("2) 更新提示词:", r.get("code"), r.get("message"))

    after = api("GET", "/workspace/%s/application/%s" % (WS, APP), tok)["data"]
    print("   校验 system 已写入:", "第二类" in ((after.get("model_setting") or {}).get("system") or ""))

    # 3) 开一个调试会话
    op = api("POST", "/workspace/%s/application/%s/open" % (WS, APP), tok, {})
    print("3) 创建会话:", op.get("code"), op.get("message"))
    chat_id = (op.get("data") or {}).get("chat_id") if isinstance(op.get("data"), dict) else None
    print("   chat_id:", chat_id)
    if not chat_id:
        print("   原始返回:", json.dumps(op, ensure_ascii=False)[:300])
        raise SystemExit(0)

    # 4) 提问
    q = "我下周去成都出差 2 晚，住宿每晚 650 块，P4 职级，一共出差 3 天，能报多少？"
    print("\n4) 提问:", q)
    out = stream_chat(tok, chat_id, q)
    print("--- 流式输出（截断 2500 字）---")
    print(out[:2500])
