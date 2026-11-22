# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, "/opt/maxkb-app"); sys.path.insert(0, "/opt/maxkb-app/apps")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxkb.settings")
import django; django.setup()
from application.models import Application, ApplicationKnowledgeMapping
from tools.models import Tool

APP = "01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"
a = Application.objects.filter(id=APP).first()
ms = a.model_setting or {}
print("model:", a.model_id)
print("tool_ids:", a.tool_ids)
print("skill_tool_ids:", a.skill_tool_ids)
print("绑定知识库数:", ApplicationKnowledgeMapping.objects.filter(application_id=APP).count())
print("system 前 60:", (ms.get("system") or "")[:60].replace("\n"," "))
print("含'第二类':", "第二类" in (ms.get("system") or ""))
print("knowledge_setting:", a.knowledge_setting)
for t in Tool.objects.filter(id__in=(a.tool_ids or []) + (a.skill_tool_ids or [])):
    print("工具:", t.name, "| type:", t.tool_type, "| is_active:", t.is_active)