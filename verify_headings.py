# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from docx import Document
d = Document(r"E:\Desktop\oncall-agent\output\星澜科技-差旅与费用报销管理办法-V2.1.docx")
h1 = [p.text for p in d.paragraphs if p.style.name == "Heading 1"]
h2 = [p.text for p in d.paragraphs if p.style.name == "Heading 2"]
print("Heading 1 数量:", len(h1))
print("Heading 2 数量:", len(h2))
print("H1 前5:", h1[:5])
print("H2 前5:", h2[:5])
from collections import Counter
print("样式分布:", Counter(p.style.name for p in d.paragraphs).most_common(5))