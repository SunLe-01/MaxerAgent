# -*- coding: utf-8 -*-
"""在容器内验证 MaxKB 的分段行为"""
import sys, os
sys.path.insert(0, "/opt/maxkb-app")
sys.path.insert(0, "/opt/maxkb-app/apps")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxkb.settings")

import django
django.setup()

from common.handle.impl.text.doc_split_handle import DocSplitHandle
from common.handle.impl.text.text_split_handle import TextSplitHandle


class FakeFile:
    def __init__(self, path):
        self.name = os.path.basename(path)
        self._path = path

    def read(self):
        with open(self._path, "rb") as f:
            return f.read()

    def seek(self, *a):
        pass


def get_buffer(f):
    return f.read()


def run(handle, path, limit, with_filter, patterns=None):
    f = FakeFile(path)
    res = handle.handle(f, patterns, with_filter, limit, get_buffer, lambda x: None)
    content = res.get("content") or []
    print("=" * 60)
    print(f"文件: {f.name} | limit={limit} with_filter={with_filter} patterns={patterns}")
    print(f"分段数: {len(content)}")
    lens = [len(c.get("content", "")) for c in content]
    if lens:
        print(f"长度: min={min(lens)} max={max(lens)} avg={sum(lens)//len(lens)}")
    for i, c in enumerate(content[:3]):
        t = c.get("title", "")
        body = c.get("content", "").replace("\n", " ")[:110]
        print(f"  [{i+1}] title={t!r}")
        print(f"       content={body}...")
    return content


if __name__ == "__main__":
    doc_handle = DocSplitHandle()
    # 1) 智能分段：默认标题正则 + 500 字
    run(doc_handle, "/tmp/test.docx", 500, False)
    # 2) 无正则（退化为按长度）
    run(doc_handle, "/tmp/test.docx", 500, False, patterns=[])
    # 3) md 文件
    md_handle = TextSplitHandle()
    run(md_handle, "/tmp/test.md", 500, False)
