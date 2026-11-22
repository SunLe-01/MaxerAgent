# -*- coding: utf-8 -*-
"""修正「差旅工作流实验」的三处问题：
import os
1. 工具节点 5 个入参：source=custom(字面文本) -> reference([节点ID, 字段名])
2. 知识库检索相似度 0.6 -> 0.35（"能报多少"类问题语义距离远，0.6 命中不了）
3. 参数提取：把职级归一化写进字段说明，避免 P4 直接进工具报错
"""
import io
import json
import sys
import urllib.error
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:8080/admin/api"
WS = "default"
APP = "01a1e2ed-1a4e-49b4-8b0d-6b1c9a8b7f3e"  # 先用列表接口取准确 ID
TOOL_NODE_ID = "eb345fc3-009c-4650-9212-fb960c8b0445"
PARAM_NODE_ID = "224ea95c-def5-4660-b7f4-055c6c91d3e7"
SEARCH_NODE_ID = "5929374a-0dc8-4515-835e-7fb37ec49d10"


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

    # 定位应用
    _, page = api("GET", f"/workspace/{WS}/application/1/50", tok)
    app = next(a for a in page["data"]["records"] if a["name"] == "差旅工作流实验")
    app_id = app["id"]
    print(f"应用: {app['name']} ({app_id})")

    _, detail = api("GET", f"/workspace/{WS}/application/{app_id}", tok)
    d = detail["data"]
    wf = d["work_flow"]

    # 建立 stepName -> nodeId 映射，用于生成引用
    name_to_id = {}
    for n in wf["nodes"]:
        name_to_id[n["properties"].get("stepName")] = n["id"]
    print("节点:", json.dumps(name_to_id, ensure_ascii=False))

    param_id = name_to_id.get("参数提取")
    changed = []

    for n in wf["nodes"]:
        p = n["properties"]
        nd = p.get("node_data") or {}

        # 1) 工具节点入参
        if n["type"] == "tool-lib-node":
            for f in nd.get("input_field_list", []):
                fname = f["name"]
                f["source"] = "reference"
                f["value"] = [param_id, fname]
                changed.append(f"tool.{fname} -> reference[{param_id},{fname}]")

        # 2) 检索相似度
        if n["type"] == "search-knowledge-node":
            ks = nd.get("knowledge_setting") or {}
            old = ks.get("similarity")
            ks["similarity"] = 0.35
            nd["knowledge_setting"] = ks
            changed.append(f"search.similarity {old} -> 0.35")

        # 3) 参数提取：给 level 加归一化说明
        if n["type"] == "parameter-extraction-node":
            for v in nd.get("variable_list", []):
                if v.get("field") == "level":
                    v["label"] = (
                        "职级，必须归一化为以下四类之一："
                        "P1-P3 / P4-P5 / M1-M2 / M3+。"
                        "用户说 P4、P5、中级、高级 → P4-P5；"
                        "P1、P2、P3 → P1-P3；M1、M2 → M1-M2；M3 及以上 → M3+"
                    )
                    changed.append("param.level 归一化说明已写入")

    payload = {"work_flow": wf}
    status, resp = api("PUT", f"/workspace/{WS}/application/{app_id}", tok, payload)
    print(f"\n保存结果: {status} code={resp.get('code')} msg={resp.get('message')}")
    for c in changed:
        print("  ✓", c)
    if status != 200 or resp.get("code") != 200:
        print("保存失败，终止")
        return

    # 发布
    status, pub = api("PUT", f"/workspace/{WS}/application/{app_id}/publish", tok, {})
    print(f"发布结果: code={pub.get('code')} msg={pub.get('message')}")


if __name__ == "__main__":
    main()
