# -*- coding: utf-8 -*-
"""第二轮修正：
import os
A. 判断器改成判断「参数是否齐全」，而不是「检索是否命中」
   —— 纯查规定类问题没有数字，走工具必然失败
B. 判断器 IF/ELSE 的连线对调：参数齐全 -> 工具 -> AI 对话；参数不全 -> 检索 -> AI 对话
   实际上更好的是：检索始终执行，判断器只管是否调工具
C. AI 对话提示词补上 {{差旅报销试算器.result}}
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

    # 节点 id 映射
    id_of = {n["properties"].get("stepName"): n["id"] for n in wf["nodes"]}
    param_id = id_of["参数提取"]
    search_id = id_of["知识库检索"]
    cond_id = id_of["判断器"]
    tool_id = id_of["差旅报销试算器"]
    chat_id = id_of["AI 对话"]
    reply_id = id_of["指定回复"]

    # 1) 参数提取：把 nights/days 等改为非必填，避免"查规定"类问题提取不到数字就报错
    for n in wf["nodes"]:
        nd = n["properties"].get("node_data") or {}
        if n["type"] == "parameter-extraction-node":
            for v in nd.get("variable_list", []):
                v["is_required"] = False
            # 提示词里说明"没有数字时输出 null"
            nd["system"] = (
                "你是信息抽取助手。从用户问题中提取差旅参数，只输出 JSON。"
                "如果某个参数在问题中没有出现，该字段输出 null，不要猜测。"
            )
            nd["prompt"] = (
                "用户问题：{{开始.question}}\n"
                "需要提取的字段：city, level, nights, hotel_price, days\n"
                "注意：level 必须归一化为 P1-P3 / P4-P5 / M1-M2 / M3+ 之一。"
            )

        # 2) 判断器：改为判断"参数齐全"（nights 不为空）
        if n["type"] == "condition-node":
            nd["branch"] = [
                {
                    "id": "if_params_ok",
                    "type": "IF",
                    "condition": "and",
                    "conditions": [
                        {"field": [param_id, "nights"], "value": 1, "compare": "is_not_null"},
                        {"field": [param_id, "hotel_price"], "value": 1, "compare": "is_not_null"},
                    ],
                },
                {"id": "else_plain", "type": "ELSE", "condition": "and", "conditions": []},
            ]
            nd["branch_condition_list"] = [
                {"index": 0, "height": 180, "id": "if_params_ok"},
                {"index": 1, "height": 44, "id": "else_plain"},
            ]

        # 3) AI 对话：补上工具结果引用
        if n["type"] == "ai-chat-node":
            nd["system"] = (
                "你是星澜科技的差旅制度答疑助手。请优先依据【参考资料】回答并标注条款；"
                "如果【试算结果】不为空，必须直接采用其中的金额数字，不要自己重算。"
                "如果参考资料为空且没有试算结果，回答：知识库中未找到相关条款，建议咨询行政人事部。"
            )
            nd["prompt"] = (
                "参考资料：{{知识库检索.data}}\n"
                "试算结果：{{差旅报销试算器.result}}\n"
                "问题：{{开始.question}}"
            )

    # 4) 重新连线：判断器 IF -> 工具 -> AI对话；ELSE -> AI对话（纯查知识库）
    new_edges = []
    for e in wf["edges"]:
        src, tgt = e["sourceNodeId"], e["targetNodeId"]
        # 去掉原来 判断器->指定回复 的边
        if src == cond_id and tgt == reply_id:
            continue
        # 判断器 -> 工具 改成锚点 if_params_ok
        if src == cond_id and tgt == tool_id:
            e["sourceAnchorId"] = f"{cond_id}_if_params_ok_right"
            new_edges.append(e)
            continue
        if src == cond_id and tgt in (tool_id, chat_id, reply_id):
            e["sourceAnchorId"] = f"{cond_id}_if_params_ok_right"
            new_edges.append(e)
            continue
        new_edges.append(e)

    # 新增：ELSE -> AI 对话
    has_else_edge = any(
        e["sourceNodeId"] == cond_id and e.get("sourceAnchorId") == f"{cond_id}_else_plain_right"
        for e in new_edges
    )
    if not has_else_edge:
        new_edges.append({
            "id": "edge_else_to_chat",
            "type": "app-edge",
            "sourceNodeId": cond_id,
            "targetNodeId": chat_id,
            "sourceAnchorId": f"{cond_id}_else_plain_right",
            "targetAnchorId": f"{chat_id}_left",
            "properties": {},
        })

    wf["edges"] = new_edges

    status, resp = api("PUT", f"/workspace/{WS}/application/{app_id}", tok, {"work_flow": wf})
    print(f"保存: {status} code={resp.get('code')} msg={resp.get('message')}")
    if resp.get("code") != 200:
        print(json.dumps(resp, ensure_ascii=False)[:500])
        return

    status, pub = api("PUT", f"/workspace/{WS}/application/{app_id}/publish", tok, {})
    print(f"发布: code={pub.get('code')} msg={pub.get('message')}")

    # 打印最终连线
    print("\n=== 最终连线 ===")
    for e in wf["edges"]:
        src = next((k for k, v in id_of.items() if v == e["sourceNodeId"]), e["sourceNodeId"][:8])
        tgt = next((k for k, v in id_of.items() if v == e["targetNodeId"]), e["targetNodeId"][:8])
        anchor = e.get("sourceAnchorId", "")
        print(f"  {src:14} -> {tgt:14} [{anchor[-20:]}]")


if __name__ == "__main__":
    main()
