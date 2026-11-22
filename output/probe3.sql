\pset pager off
\echo '=== version flags ==='
select name, tool_enable, tool_ids, skill_tool_ids, mcp_enable,
       jsonb_array_length(coalesce(knowledge_ids,'[]'::jsonb)) as kb_count,
       model_id
from application_version order by create_time desc limit 2;
\echo '=== embedding source_type 1 sample ==='
select e.source_type, count(*) filter (where p.id is not null) as matched_paragraph,
       count(*) filter (where p.id is null) as unmatched
from embedding e left join paragraph p on p.id = e.paragraph_id
group by e.source_type;
\echo '=== embedding paragraph_id null? ==='
select column_name from information_schema.columns where table_name='embedding' order by ordinal_position;
