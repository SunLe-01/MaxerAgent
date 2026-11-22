# -*- coding: utf-8 -*-
import sys, os, json, asyncio
sys.path.insert(0, "/opt/maxkb-app"); sys.path.insert(0, "/opt/maxkb-app/apps")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxkb.settings")
import django; django.setup()
from tools.models import Tool
from common.utils.tool_code import ToolExecutor

TOOL="01a1ded0-6d64-7eb1-a63d-6367d38f8fcf"
t=Tool.objects.filter(id=TOOL).first()
ex=ToolExecutor()
cfg=ex.get_tool_mcp_config(t, {})
print("MCP 配置:", json.dumps(cfg, ensure_ascii=False)[:600])

from langchain_mcp_adapters.client import MultiServerMCPClient
async def main():
    client = MultiServerMCPClient({str(t.id): cfg})
    try:
        tools = await asyncio.wait_for(client.get_tools(), timeout=60)
        print("MCP 暴露的工具数:", len(tools))
        for x in tools: print("  -", x.name, "|", (x.description or "")[:40])
    except Exception as e:
        print("MCP 启动失败:", type(e).__name__, str(e)[:400])
asyncio.run(main())