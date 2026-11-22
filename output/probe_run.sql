\pset pager off
\echo '=== 该应用最近的对话记录 ==='
select to_char(create_time,'HH24:MI:SS') as t,
       left(problem_text, 40) as question,
       left(answer_text, 60) as answer,
       length(details::text) as details_len
from application_chat_record
where chat_id in (select id from application_chat
                  where application_id = (select id from application where name='差旅工作流实验'))
order by create_time desc limit 5;

\echo '=== details 的顶层 key（看走了哪些节点）==='
select jsonb_object_keys(details::jsonb) as step_key,
       left(details::jsonb->jsonb_object_keys(details::jsonb)::text, 0) as x
from application_chat_record
where chat_id in (select id from application_chat
                  where application_id = (select id from application where name='差旅工作流实验'))
order by create_time desc limit 40;
