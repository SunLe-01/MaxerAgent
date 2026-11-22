\pset pager off
\echo '=== 知识库检索节点配置 ==='
select n->'properties'->>'stepName' as step_name,
       n->'properties'->'node_data'->>'knowledge_id_list' as kb_ids,
       n->'properties'->'node_data'->>'question_reference_address' as q_ref,
       n->'properties'->'node_data'->'knowledge_setting'->>'top_n' as top_n,
       n->'properties'->'node_data'->'knowledge_setting'->>'similarity' as sim,
       n->'properties'->'node_data'->'knowledge_setting'->>'search_mode' as mode
from application,
     jsonb_array_elements(work_flow::jsonb->'nodes') n
where name = '差旅工作流实验' and n->>'type' = 'search-knowledge-node';

\echo '=== 参数提取节点配置 ==='
select n->'properties'->>'stepName' as step_name,
       n->'properties'->'node_data'->>'input_variable' as input_var,
       n->'properties'->'node_data'->'variable_list' as var_list,
       n->'properties'->'node_data'->>'model_id' as model_id
from application,
     jsonb_array_elements(work_flow::jsonb->'nodes') n
where name = '差旅工作流实验' and n->>'type' = 'parameter-extraction-node';

\echo '=== 判断器配置 ==='
select n->'properties'->>'stepName' as step_name,
       n->'properties'->'node_data'->'branch' as branch
from application,
     jsonb_array_elements(work_flow::jsonb->'nodes') n
where name = '差旅工作流实验' and n->>'type' = 'condition-node';

\echo '=== 工具节点入参映射 ==='
select n->'properties'->'node_data' as tool_node_data
from application,
     jsonb_array_elements(work_flow::jsonb->'nodes') n
where name = '差旅工作流实验' and n->>'type' = 'tool-lib-node';
