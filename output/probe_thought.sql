\pset pager off
\echo '=== 最近一次 SIMPLE 应用对话：是否记录了推理过程 ==='
select to_char(create_time,'HH24:MI:SS') as t,
       length(details::text) as details_len,
       (details::jsonb->'chat_step'->'message_list'->0->>'content') is not null as has_msg
from application_chat_record
where chat_id in (select id from application_chat
                  where application_id = '01a1de97-cfe1-7f23-baa8-9caf5bdc25a8')
order by create_time desc limit 3;

\echo '=== answer_text 里是否含 reasoning / think 标记 ==='
select to_char(create_time,'HH24:MI:SS') as t,
       position('think' in answer_text) > 0 as has_think,
       position('reasoning' in answer_text) > 0 as has_reasoning,
       left(answer_text, 80) as head
from application_chat_record
where chat_id in (select id from application_chat
                  where application_id = '01a1de97-cfe1-7f23-baa8-9caf5bdc25a8')
order by create_time desc limit 2;
