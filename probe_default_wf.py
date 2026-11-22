# -*- coding: utf-8 -*-
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

d = json.load(open(r"MaxKB\apps\application\flow\default_workflow_zh.json", encoding="utf-8"))
print("top keys:", list(d.keys()))
print("\n=== nodes ===")
for n in d.get("nodes", []):
    p = n.get("properties", {}) or {}
    nd = p.get("node_data", {}) or {}
    extra = ""
    if n.get("type") == "search-knowledge-node":
        extra = f"kb={nd.get('knowledge_id_list')} topn={nd.get('top_n')}"
    if n.get("type") == "ai-chat-node":
        extra = f"model={str(nd.get('model_id'))[:8]}"
    print(f"{n.get('type'):26} {p.get('stepName',''):12} x={n.get('x'):<5} y={n.get('y'):<4} {extra}")

print("\n=== edges ===")
for e in d.get("edges", []):
    print(f"{e.get('sourceNodeId'):20} -> {e.get('targetNodeId'):20} anchor={e.get('sourceAnchorId')}")
