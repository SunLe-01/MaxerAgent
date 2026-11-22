\pset pager off
\echo '=== 工具节点 input_field_list 当前存储 ==='
select jsonb_pretty(n->'properties'->'node_data'->'input_field_list')
from application,
     jsonb_array_elements(work_flow::jsonb->'nodes') n
where name = '差旅工作流实验' and n->>'type' = 'tool-lib-node';

\echo '=== 节点是否有其他位置存 input_field_list ==='
select n->'properties' as props
from application,
     jsonb_array_elements(work_flow::jsonb->'nodes') n
where name = '差旅工作流实验' and n->>'type' = 'tool-lib-node';
