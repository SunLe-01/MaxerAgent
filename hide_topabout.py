# -*- coding: utf-8 -*-
"""向容器内已构建的 admin/index.html 注入一段样式，隐藏顶栏 TopAbout 整组按钮。
说明：这是「免重建」的临时生效方式；源码已同步修改，正式做法仍是重新构建前端。
"""
import io
import shutil
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

P = "/opt/maxkb-app/apps/static/admin/index.html"
BAK = P + ".bak"

STYLE = (
    '<style id="dsh-hide-topabout">'
    "div.top-about{display:none !important;}"
    "</style>"
)

with open(P, encoding="utf-8") as f:
    html = f.read()

if "dsh-hide-topabout" in html:
    print("已注入过，跳过")
    sys.exit(0)

shutil.copyfile(P, BAK)
print("已备份 ->", BAK)

if "</head>" in html:
    html = html.replace("</head>", STYLE + "</head>", 1)
elif "<body" in html:
    html = html.replace("<body", STYLE + "<body", 1)
else:
    print("未找到注入点")
    sys.exit(1)

with open(P, "w", encoding="utf-8") as f:
    f.write(html)

print("注入完成，当前长度:", len(html))
print("校验:", "dsh-hide-topabout" in open(P, encoding="utf-8").read())
