\pset pager off
\echo '=== embedding by source_type ==='
select source_type, count(*) from embedding group by source_type;
\echo '=== embedded paragraph dims ==='
select vector_dims(embedding) as dims, count(*) from embedding group by 1;
\echo '=== pgvector version ==='
select extversion from pg_extension where extname='vector';
\echo '=== app dialogue_number / top_n ==='
select dialogue_number, knowledge_setting->>'top_n' as top_n, knowledge_setting->>'similarity' as sim,
       knowledge_setting->>'search_mode' as mode, long_term_enable, mcp_enable, tool_enable, application_enable
from application;
