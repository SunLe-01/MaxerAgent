# -*- coding: utf-8 -*-
"""按运行时真实语义修正工具节点入参。

import os
根因：base_tool_lib_node.py 的 execute() 里
    { 'value': get_field_value(node_input_field_list, name, required), **tool_def_field }
source 取自 **工具定义** tool.input_field_list，恒为 'custom'，
所以永远走 generate_prompt(模板字符串) 分支，而不是 reference 数组分支。
=> 节点入参必须写成 Jinja 模板字符串 "{{参数提取.city}}"。
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
PARAM_STEP = "参数提取"


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

    for n in wf["nodes"]:
        nd = n["properties"].get("node_data") or {}
        if n["type"] == "tool-lib-node":
            for f in nd.get("input_field_list", []):
                # 写成 Jinja 模板字符串，交给 generate_prompt 解析
                f["value"] = "{{" + f"{PARAM_STEP}.{f['name']}" + "}}"
                f["source"] = "custom"
                print(f"  {f['name']:12} -> {f['value']}")

    status, resp = api("PUT", f"/workspace/{WS}/application/{app_id}", tok, {"work_flow": wf})
    print(f"\n保存: {status} code={resp.get('code')} msg={resp.get('message')}")
    if resp.get("code") != 200:
        return

    status, pub = api("PUT", f"/workspace/{WS}/application/{app_id}/publish", tok, {})
    print(f"发布: code={pub.get('code')} msg={pub.get('message')}")


if __name__ == "__main__":
    main()
