\pset pager off
\echo '=== 上下文构成：字符数 vs message_tokens ==='
select to_char(create_time,'HH24:MI:SS') t,
       message_tokens,
       (select sum(length(m->>'content'))
          from jsonb_array_elements(details::jsonb->'chat_step'->'message_list') m) as total_msg_chars,
       jsonb_array_length(details::jsonb->'chat_step'->'message_list') as msgs,
       round(message_tokens::numeric /
             nullif((select sum(length(m->>'content'))
                from jsonb_array_elements(details::jsonb->'chat_step'->'message_list') m),0), 2) as tokens_per_char
from application_chat_record
where create_time::date = current_date
order by create_time;
\echo '=== 每条 message 的角色与长度 ==='
select to_char(r.create_time,'HH24:MI:SS') t,
       m->>'role' as role,
       length(m->>'content') as chars,
       left(replace(m->>'content', chr(10), ' '), 70) as preview
from application_chat_record r,
     jsonb_array_elements(r.details::jsonb->'chat_step'->'message_list') m
where r.create_time::date = current_date
order by r.create_time, 1;
