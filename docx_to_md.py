# -*- coding: utf-8 -*-
"""把生成的制度 docx 转成 Markdown（便于知识库自动分段）"""
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

SRC = r"E:\Desktop\oncall-agent\output\星澜科技-差旅与费用报销管理办法-V2.1.docx"
DST = r"E:\Desktop\oncall-agent\output\星澜科技-差旅与费用报销管理办法-V2.1.md"

doc = Document(SRC)


def iter_block_items(document):
    body = document.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def table_to_md(table):
    rows = []
    for r in table.rows:
        cells = [c.text.replace("\n", " ").replace("|", "\\|").strip() for c in r.cells]
        rows.append(cells)
    if not rows:
        return ""
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |",
             "|" + "|".join([" --- "] * ncol) + "|"]
    for r in rows[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


out = []
for block in iter_block_items(doc):
    if isinstance(block, Paragraph):
        text = block.text.strip()
        if not text:
            continue
        style = block.style.name if block.style is not None else "Normal"
        if style == "Heading 1":
            out.append(f"\n# {text}\n")
        elif style == "Heading 2":
            out.append(f"\n## {text}\n")
        else:
            # 第一条 目的 这类正文小标题（加粗短段落）保留为普通段落
            out.append(text)
    else:
        md = table_to_md(block)
        if md:
            out.append("\n" + md + "\n")

md_text = "\n\n".join(out)
os.makedirs(os.path.dirname(DST), exist_ok=True)
with open(DST, "w", encoding="utf-8") as f:
    f.write(md_text)

print("saved:", DST)
print("字符数:", len(md_text))
print("一级标题:", md_text.count("\n# "))
print("二级标题:", md_text.count("\n## "))
