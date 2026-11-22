\pset pager off
\echo '=== 工具节点 input_field_list 当前存储 ==='
select jsonb_pretty(n->'properties'->'node_data'->'input_field_list')
from application,
     jsonb_array_elements(work_flow::jsonb->'nodes') n
where name = '差旅工作流实验' and n->>'type' = 'tool-lib-node';

\echo '=== 最近一次报错记录 ==='
select to_char(create_time,'HH24:MI:SS') as t,
       left(answer_text, 200) as answer
from application_chat_record
where chat_id in (select id from application_chat
                  where application_id = (select id from application where name='差旅工作流实验'))
order by create_time desc limit 3;
