\pset pager off
\echo '=== 应用列表 ==='
select left(id::text, 12) as id, name, type, is_publish,
       to_char(create_time,'MM-DD HH24:MI') as created
from application order by create_time;
\echo '=== 新应用的工作流节点 ==='
select jsonb_array_length(work_flow::jsonb->'nodes') as node_count,
       jsonb_array_length(work_flow::jsonb->'edges') as edge_count
from application where name = '差旅工作流实验';
