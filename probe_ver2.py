# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, "/opt/maxkb-app"); sys.path.insert(0, "/opt/maxkb-app/apps")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxkb.settings")
import django; django.setup()
from application.models import ApplicationVersion
APP = "01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"
v = ApplicationVersion.objects.filter(application_id=APP).order_by("-create_time").first()
print("最新版本时间:", v.create_time)
print("knowledge_ids:", getattr(v, "knowledge_ids", "N/A"))
print("tool_ids:", v.tool_ids)
print("skill_tool_ids:", v.skill_tool_ids)
print("model:", v.model)
print("knowledge_setting:", v.knowledge_setting)