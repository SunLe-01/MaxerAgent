# -*- coding: utf-8 -*-
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from docx import Document
p = r"E:\Desktop\oncall-agent\output\星澜科技-差旅与费用报销管理办法-V2.1.docx"
d = Document(p)
print("段落数:", len(d.paragraphs), " 表格数:", len(d.tables))
chars = sum(len(x.text) for x in d.paragraphs) + sum(len(c.text) for t in d.tables for r in t.rows for c in r.cells)
print("总字符数(含表格):", chars)
print("--- 章节标题 ---")
for x in d.paragraphs:
    t = x.text.strip()
    if t.startswith("第") and ("章" in t[:5] or "条" in t[:6]) or t.startswith("附录"):
        print("  ", t)
print("--- 表格规模 ---")
for i, t in enumerate(d.tables, 1):
    print(f"  表{i}: {len(t.rows)}行 x {len(t.columns)}列 | 首行: {t.rows[0].cells[0].text[:20]}")
print("--- 抽查内容 ---")
for kw in ["600", "3,000", "80 美元", "15 个工作日", "qwen"]:
    hit = any(kw in c.text for t in d.tables for r in t.rows for c in r.cells) or any(kw in x.text for x in d.paragraphs)
    print(f"  包含 {kw!r}: {hit}")