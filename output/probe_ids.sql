\pset pager off
\echo '=== 全部节点的 id 与类型（核对判断器引用的 id 是否存在）==='
select n->>'id' as node_id, n->>'type' as node_type,
       n->'properties'->>'stepName' as step_name
from application,
     jsonb_array_elements(work_flow::jsonb->'nodes') n
where name = '差旅工作流实验'
order by 2;

\echo '=== 判断器引用 id: 5929374a-0dc8-4515-835e-7fb37ec49d10 是否存在 ==='
select count(*) as exists_count
from application,
     jsonb_array_elements(work_flow::jsonb->'nodes') n
where name = '差旅工作流实验'
  and n->>'id' = '5929374a-0dc8-4515-835e-7fb37ec49d10';

\echo '=== 连线（source -> target）==='
select e->>'sourceNodeId' as src, e->>'targetNodeId' as tgt,
       e->>'sourceAnchorId' as anchor
from application,
     jsonb_array_elements(work_flow::jsonb->'edges') e
where name = '差旅工作流实验';
