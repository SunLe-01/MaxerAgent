# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, "/opt/maxkb-app"); sys.path.insert(0, "/opt/maxkb-app/apps")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxkb.settings")
import django; django.setup()
from application.models import Application, ApplicationVersion

APP = "01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"
a = Application.objects.filter(id=APP).first()
print("is_publish:", a.is_publish)
vs = ApplicationVersion.objects.filter(application_id=APP).order_by("-create_time")[:5]
print("发布版本数:", ApplicationVersion.objects.filter(application_id=APP).count())
for v in vs:
    print("-"*60)
    print("版本时间:", v.create_time.strftime("%m-%d %H:%M"))
    print("tool_ids:", getattr(v, "tool_ids", "N/A"))
    print("skill_tool_ids:", getattr(v, "skill_tool_ids", "N/A"))
    ms = v.model_setting or {}
    print("system 含'第二类':", "第二类" in ((ms.get("system") or "")))
    print("system 前 40:", (ms.get("system") or "")[:40].replace("\n"," "))