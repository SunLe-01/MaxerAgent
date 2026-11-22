# -*- coding: utf-8 -*-
"""上传技能包、创建 SKILL 工具、挂到智能体"""
import json
import os
import urllib.request
import uuid

BASE = "http://127.0.0.1:8080/admin/api"
WS = "default"
APP_ID = "01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"
TOOL_ID = "01a1ded0-6d64-7eb1-a63d-6367d38f8fcf"
ZIP = r"E:\Desktop\oncall-agent\output\travel-expense-audit.zip"


def req(method, path, token=None, body=None, raw=None, ctype=None):
    headers = {}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif raw is not None:
        data = raw
        headers["Content-Type"] = ctype
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        txt = e.read().decode("utf-8", "replace")
        try:
            return json.loads(txt)
        except Exception:
            return {"code": e.code, "message": txt}


def multipart(file_path, field="file"):
    boundary = "----dsh" + uuid.uuid4().hex
    name = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        content = f.read()
    parts = []
    parts.append(("--" + boundary).encode())
    parts.append(('Content-Disposition: form-data; name="%s"; filename="%s"' % (field, name)).encode("utf-8"))
    parts.append(b"Content-Type: application/zip")
    parts.append(b"")
    parts.append(content)
    parts.append(("--" + boundary + "--").encode())
    parts.append(b"")
    return b"\r\n".join(parts), "multipart/form-data; boundary=" + boundary


if __name__ == "__main__":
    tok = req("POST", "/user/login", body={"username": "admin", "password": os.getenv("MAXKB_PASSWORD", "")})["data"]["token"]
    print("1) 登录 OK")

    raw, ctype = multipart(ZIP)
    up = req("PUT", "/workspace/%s/tool/upload_skill_file" % WS, tok, raw=raw, ctype=ctype)
    print("2) 上传技能包:", up.get("code"), up.get("message"))
    data = up.get("data")
    file_id = data.get("id") if isinstance(data, dict) else (data if isinstance(data, str) else None)
    print("   file_id:", file_id)
    if not file_id:
        print("   原始返回:", json.dumps(up, ensure_ascii=False)[:400])
        raise SystemExit(1)

    skill_payload = {
        "name": "差旅报销单审核",
        "desc": "审核差旅报销单是否符合公司《差旅与费用报销管理办法 V2.1》：检查时效、住宿标准、伙食补贴、市内交通限额、单据完整性与常见违规，输出问题清单与修改建议。当用户提供报销明细要求审核时使用。",
        "tool_type": "SKILL",
        "code": file_id,
        "input_field_list": [],
        "init_field_list": [],
        "is_active": True,
        "scope": "WORKSPACE",
    }
    sk = req("POST", "/workspace/%s/tool" % WS, tok, skill_payload)
    print("3) 创建技能工具:", sk.get("code"), sk.get("message"))
    skill_id = (sk.get("data") or {}).get("id")
    print("   skill_id:", skill_id)

    # 4) 挂到智能体
    app = req("GET", "/workspace/%s/application/%s" % (WS, APP_ID), tok)["data"]
    payload = {
        "name": app.get("name"),
        "desc": app.get("desc"),
        "tool_ids": [TOOL_ID],
        "skill_tool_ids": [skill_id] if skill_id else [],
    }
    up2 = req("PUT", "/workspace/%s/application/%s" % (WS, APP_ID), tok, payload)
    print("4) 挂载到智能体:", up2.get("code"), up2.get("message"))

    after = req("GET", "/workspace/%s/application/%s" % (WS, APP_ID), tok)["data"]
    print("\n=== 智能体当前配置 ===")
    print("名称:", after.get("name"))
    print("工具:", [t.get("name") for t in (after.get("tool_list") or [])])
    print("技能:", [t.get("name") for t in (after.get("skill_tool_list") or [])])
    print("tool_ids:", after.get("tool_ids"))
    print("skill_tool_ids:", after.get("skill_tool_ids"))
