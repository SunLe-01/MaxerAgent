# -*- coding: utf-8 -*-
import sys, os, json
sys.path.insert(0, "/opt/maxkb-app"); sys.path.insert(0, "/opt/maxkb-app/apps")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxkb.settings")
import django; django.setup()
from application.flow.tools import get_tools
from tools.models import Tool
from models_provider.models import Model

TOOL="01a1ded0-6d64-7eb1-a63d-6367d38f8fcf"
SKILL="01a1ded0-bc5b-7953-a34f-b0fd200e88fb"
APP="01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"
UID="f0dd8f71-e4ee-11ee-8c84-a8a1595801ab"

for tid in (TOOL, SKILL):
    t=Tool.objects.filter(id=tid).first()
    print("工具记录:", tid, "->", None if not t else (t.name, t.tool_type, t.is_active, "code="+str(t.code)[:40]))

ts = get_tools("APPLICATION", APP, [TOOL], "default", UID)
print("get_tools 返回数量:", len(ts))
for x in ts:
    print("  ", getattr(x,"name",x))