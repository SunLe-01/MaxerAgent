# -*- coding: utf-8 -*-
"""为「差旅制度答疑」智能体创建可用的工具与技能"""
import json
import urllib.request
import zipfile
import os
import io

BASE = "http://127.0.0.1:8080/admin/api"
WS = "default"
APP_ID = "01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"


def api(method, path, token=None, body=None):
    url = BASE + path
    data = None
    headers = {}
    if token:
        headers["Authorization"] = "Bearer " + token
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"code": e.code, "message": e.read().decode("utf-8", "replace")}


def login():
    r = api("POST", "/user/login", body={"username": "admin", "password": os.getenv("MAXKB_PASSWORD", "")})
    return r["data"]["token"]


TOOL_CODE = '''def main(city: str, level: str, nights: int, hotel_price: float, days: int) -> dict:
    tier1 = ["北京", "上海", "广州", "深圳"]
    tier2 = ["杭州", "成都", "南京", "武汉", "西安", "苏州", "天津", "重庆", "长沙", "郑州",
             "青岛", "宁波", "厦门", "合肥", "济南", "福州", "东莞", "佛山"]

    city = (city or "").strip()
    if city in tier1:
        tier, idx = "一类", 0
    elif city in tier2:
        tier, idx = "二类", 1
    else:
        tier, idx = "三类", 2

    lodging_cap = {
        "P1-P3": [600, 450, 350],
        "P4-P5": [700, 550, 450],
        "M1-M2": [900, 700, 600],
        "M3+":   [1200, 1000, 800],
    }
    meal_std = [100, 80, 60]

    key = (level or "").strip().upper().replace("—", "-").replace("－", "-")
    if key not in lodging_cap:
        return {"error": "职级不支持：" + str(level) + "，请使用 P1-P3 / P4-P5 / M1-M2 / M3+"}

    cap_per_night = lodging_cap[key][idx]
    nights = int(nights or 0)
    days = int(days or 0)
    hotel_price = float(hotel_price or 0)

    lodging_actual = round(hotel_price * nights, 2)
    lodging_cap_total = cap_per_night * nights
    lodging_reimbursable = min(lodging_actual, lodging_cap_total)
    lodging_over = round(max(lodging_actual - lodging_cap_total, 0), 2)

    meal_per_day = meal_std[idx]
    meal_total = meal_per_day * days

    notes = []
    if lodging_over > 0:
        notes.append("住宿超标 %.2f 元，超标部分需自付；特殊情况须书面说明并经分管副总批准" % lodging_over)
    if nights == 0:
        notes.append("当日往返：伙食补贴按标准的 50% 计发（%d 元/天）" % (meal_per_day // 2))
        meal_total = (meal_per_day // 2) * days
    notes.append("市内交通每日限额：一类 200 元 / 二类 150 元 / 三类 120 元")

    return {
        "query": {"city": city, "level": key, "nights": nights, "hotel_price": hotel_price, "days": days},
        "city_tier": tier,
        "lodging_cap_per_night": cap_per_night,
        "lodging_cap_total": lodging_cap_total,
        "lodging_actual": lodging_actual,
        "lodging_reimbursable": round(lodging_reimbursable, 2),
        "lodging_over": lodging_over,
        "meal_allowance_per_day": (meal_per_day // 2) if nights == 0 else meal_per_day,
        "meal_allowance_total": meal_total,
        "travel_total_reimbursable": round(lodging_reimbursable + meal_total, 2),
        "notes": notes,
    }
'''

SKILL_MD = '''---
name: travel-expense-audit
description: 审核差旅报销单是否符合公司《差旅与费用报销管理办法 V2.1》。当用户贴出报销明细、发票信息、出差日期与金额，要求"帮我看看能不能报""审核一下这笔报销"时使用。输出问题清单与修改建议。
---

# 差旅报销单审核

## 何时使用
- 用户给出报销明细（日期、城市、住宿费、交通费、补贴），问"能报吗""有没有问题"
- 用户贴出发票信息，问抬头/税号/金额是否合规
- 用户不确定是否超期、是否超标

## 审核步骤（按顺序执行）

1. **时效检查**：出差结束后 15 个工作日内提交；跨年度须在当年 12 月 25 日前；超期 30 天原则上不受理（可申请一次例外，需总经理批准）。
2. **城市分级**：北京/上海/广州/深圳 = 一类；杭州、成都、南京、武汉、西安、苏州、天津、重庆、长沙、郑州、青岛、宁波、厦门、合肥、济南、福州、东莞、佛山 = 二类；其余 = 三类。
3. **住宿标准**（元/晚，含税）：
   - P1-P3：一类 600 / 二类 450 / 三类 350
   - P4-P5：一类 700 / 二类 550 / 三类 450
   - M1-M2：一类 900 / 二类 700 / 三类 600
   - M3 及以上：一类 1200 / 二类 1000 / 三类 800
4. **伙食补贴**（元/天，包干无需发票）：一类 100、二类 80、三类 60；当日往返按 50% 计发；会议/培训统一安排用餐的不发。
5. **市内交通限额**：一类 200 / 二类 150 / 三类 120 元/天。
6. **单据完整**：增值税发票（抬头"星澜信息技术有限公司"+ 正确税号）、机票行程单、火车票、住宿发票及水单（须体现入住人与天数）、出差申请单编号。
7. **常见违规**：虚开发票、重复报销、拆分报销规避审批、个人消费混入、超期未报。

## 输出格式

```
### 审核结论：通过 / 有问题 / 无法判断

**逐项检查**
| 检查项 | 结果 | 说明 |
|---|---|---|
| 时效 | ✅/⚠️/❌ | ... |
| 住宿标准 | ... | ... |
| 伙食补贴 | ... | ... |
| 市内交通 | ... | ... |
| 单据完整 | ... | ... |

**需要你补充**
- ...

**依据**
- 第X条 ...
```

## 注意事项
- 只依据上述标准判断，不要臆造条款；标准里没有的项目（如境外、长期驻场）提示"请参考第十九条/第十四条"。
- 金额一律保留两位小数。
- 若用户未提供职级，必须先问职级再判断住宿标准。
'''

AUDIT_PY = '''# -*- coding: utf-8 -*-
"""可选辅助脚本：差旅报销单审核
用法: python audit.py '{"city":"成都","level":"P4-P5","nights":2,"hotel_price":650,"days":3}'
"""
import json
import sys

TIER1 = {"北京", "上海", "广州", "深圳"}
TIER2 = {"杭州", "成都", "南京", "武汉", "西安", "苏州", "天津", "重庆", "长沙", "郑州",
         "青岛", "宁波", "厦门", "合肥", "济南", "福州", "东莞", "佛山"}
LODGING = {"P1-P3": [600, 450, 350], "P4-P5": [700, 550, 450],
           "M1-M2": [900, 700, 600], "M3+": [1200, 1000, 800]}
MEAL = [100, 80, 60]


def main(data: dict) -> dict:
    city = data.get("city", "")
    idx = 0 if city in TIER1 else (1 if city in TIER2 else 2)
    tier = ["一类", "二类", "三类"][idx]
    level = data.get("level", "").upper()
    if level not in LODGING:
        return {"error": "职级不支持，请用 P1-P3 / P4-P5 / M1-M2 / M3+"}
    cap = LODGING[level][idx]
    nights = int(data.get("nights", 0))
    price = float(data.get("hotel_price", 0))
    days = int(data.get("days", 0))
    over = max(price - cap, 0) * nights
    meal = (MEAL[idx] // 2 if nights == 0 else MEAL[idx]) * days
    return {
        "city_tier": tier,
        "lodging_cap_per_night": cap,
        "lodging_over_total": round(over, 2),
        "meal_total": meal,
        "reimbursable_total": round(min(price * nights, cap * nights) + meal, 2),
    }


if __name__ == "__main__":
    payload = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(main(payload), ensure_ascii=False, indent=2))
'''


def build_skill_zip(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("travel-expense-audit/SKILL.md", SKILL_MD)
        z.writestr("travel-expense-audit/audit.py", AUDIT_PY)
    return path


if __name__ == "__main__":
    token = login()
    print("登录成功")

    # ---------- 1. 创建工具 ----------
    tool_payload = {
        "name": "差旅报销试算器",
        "desc": "根据城市、职级、住宿晚数、实际房价和出差天数，计算本次出差的住宿可报上限、伙食补贴、超标金额与合计可报金额。当用户问『我这次出差能报多少』『住宿超标多少』时调用。",
        "tool_type": "CUSTOM",
        "code": TOOL_CODE,
        "input_field_list": [
            {"name": "city", "type": "string", "source": "custom", "is_required": True},
            {"name": "level", "type": "string", "source": "custom", "is_required": True},
            {"name": "nights", "type": "int", "source": "custom", "is_required": True},
            {"name": "hotel_price", "type": "float", "source": "custom", "is_required": True},
            {"name": "days", "type": "int", "source": "custom", "is_required": True},
        ],
        "init_field_list": [],
        "is_active": True,
        "scope": "WORKSPACE",
    }
    r = api("POST", "/workspace/%s/tool" % WS, token, tool_payload)
    print("创建工具:", r.get("code"), r.get("message"))
    tool_id = r.get("data", {}).get("id") if r.get("data") else None
    print("工具 id:", tool_id)

    # ---------- 2. 调试工具 ----------
    dbg = {
        "code": TOOL_CODE,
        "input_field_list": tool_payload["input_field_list"],
        "init_field_list": [],
        "init_params": {},
        "debug_field_list": [
            {"name": "city", "value": "成都"},
            {"name": "level", "value": "P4-P5"},
            {"name": "nights", "value": "2"},
            {"name": "hotel_price", "value": "650"},
            {"name": "days", "value": "3"},
        ],
    }
    d = api("POST", "/workspace/%s/tool/debug" % WS, token, dbg)
    print("调试:", d.get("code"), d.get("message"))
    print("调试结果:", json.dumps(d.get("data"), ensure_ascii=False))

    # ---------- 3. 打包技能 ----------
    zip_path = r"E:\Desktop\oncall-agent\output\travel-expense-audit.zip"
    build_skill_zip(zip_path)
    print("技能包:", zip_path, os.path.getsize(zip_path), "bytes")
