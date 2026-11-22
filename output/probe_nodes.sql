\pset pager off
\echo '=== 各节点关键配置 ==='
select n->>'type' as node_type,
       n->'properties'->>'stepName' as step_name,
       left(n->'properties'->'node_data'::text, 0) as dummy,
       n->'properties'->'node_data' as node_data
from application,
     jsonb_array_elements(work_flow::jsonb->'nodes') n
where name = '差旅工作流实验';
