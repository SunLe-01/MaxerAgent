# -*- coding: utf-8 -*-
"""第四轮修正：
import os
AI 对话节点有两条入边（来自工具 和 判断器ELSE），但节点默认 condition='AND'，
要求所有上游都执行过 -> 走 ELSE 时工具没执行，AI 对话被跳过，答案为空。
代码依据（workflow_manage.get_next_node_list）：
    if next_node.properties.get('condition', "AND") == 'AND':
        if self.dependent_node_been_executed(edge.targetNodeId): ...
    else:
        node_list.append(...)   # OR 时直接加入，不校验依赖
所以把 AI 对话 的 condition 改成 'OR'。
同时删除已孤立的「指定回复」节点（不再有入边）。
"""
import io
import json
import sys
import urllib.error
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8080/admin/api"
WS = "default"
APP_NAME = "差旅工作流实验"


def api(method, path, token=None, body=None, timeout=120):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8", "replace") or "{}")


def main():
    _, login = api("POST", "/user/login", body={"username": "admin", "password": os.getenv("MAXKB_PASSWORD", "")})
    tok = login["data"]["token"]
    _, page = api("GET", f"/workspace/{WS}/application/1/50", tok)
    app = next(a for a in page["data"]["records"] if a["name"] == APP_NAME)
    app_id = app["id"]

    _, detail = api("GET", f"/workspace/{WS}/application/{app_id}", tok)
    wf = detail["data"]["work_flow"]

    id_of = {n["properties"].get("stepName"): n["id"] for n in wf["nodes"]}
    reply_id = id_of.get("指定回复")

    for n in wf["nodes"]:
        if n["type"] == "ai-chat-node":
            n["properties"]["condition"] = "OR"
            print(f"AI 对话 condition -> OR")

    # 删除孤立节点「指定回复」及其相关边
    if reply_id:
        wf["nodes"] = [n for n in wf["nodes"] if n["id"] != reply_id]
        wf["edges"] = [e for e in wf["edges"]
                       if e["sourceNodeId"] != reply_id and e["targetNodeId"] != reply_id]
        print("已删除孤立的「指定回复」节点")

    status, resp = api("PUT", f"/workspace/{WS}/application/{app_id}", tok, {"work_flow": wf})
    print(f"保存: {status} code={resp.get('code')} msg={resp.get('message')}")
    if resp.get("code") != 200:
        return

    status, pub = api("PUT", f"/workspace/{WS}/application/{app_id}/publish", tok, {})
    print(f"发布: code={pub.get('code')} msg={pub.get('message')}")

    print("\n=== 最终连线 ===")
    for e in wf["edges"]:
        src = next((k for k, v in id_of.items() if v == e["sourceNodeId"]), e["sourceNodeId"][:8])
        tgt = next((k for k, v in id_of.items() if v == e["targetNodeId"]), e["targetNodeId"][:8])
        print(f"  {src:12} -> {tgt:12} [{e.get('sourceAnchorId','')[-18:]}]")


if __name__ == "__main__":
    main()
