# -*- coding: utf-8 -*-
"""检查 MaxKB 向量库的实际索引与扩展版本"""
import sys, os
sys.path.insert(0, "/opt/maxkb-app")
sys.path.insert(0, "/opt/maxkb-app/apps")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "maxkb.settings")
import django
django.setup()
from django.db import connection

with connection.cursor() as cur:
    cur.execute("select extname, extversion from pg_extension where extname in ('vector')")
    print("pgvector 扩展:", cur.fetchall())

    cur.execute("select indexname, indexdef from pg_indexes where tablename='embedding'")
    print("\nembedding 表索引:")
    for name, ddl in cur.fetchall():
        print(f"  - {name}\n    {ddl}")

    cur.execute("select count(*), min(vector_dims(embedding::vector)), max(vector_dims(embedding::vector)) from embedding")
    print("\n向量行数 / 维度:", cur.fetchall())

    # HNSW 运行时参数
    cur.execute("show hnsw.ef_search")
    print("hnsw.ef_search:", cur.fetchone())
