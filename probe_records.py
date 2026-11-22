# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, "/opt/maxkb-app"); sys.path.insert(0, "/opt/maxkb-app/apps")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxkb.settings")
import django; django.setup()
from application.models import ChatRecord, Chat

APP = "01a1de97-cfe1-7f23-baa8-9caf5bdc25a8"
chat_ids = list(Chat.objects.filter(application_id=APP).values_list("id", flat=True))
print("会话数:", len(chat_ids))
rows = ChatRecord.objects.filter(chat_id__in=chat_ids).order_by("-create_time")[:8]
print("最近 8 条（新→旧）")
for r in rows:
    ans = r.answer_text or ""
    print("-"*70)
    print("时间:", r.create_time.strftime("%H:%M:%S"), "| 含工具调用:", "<tool_calls_render>" in ans)
    print("问:", (r.problem_text or "")[:40])
    print("答:", ans.replace("\n"," ")[:100])