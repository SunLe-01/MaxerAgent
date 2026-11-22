\pset pager off
\echo '=== 今天各条记录：system prompt 长度 vs 总 message_tokens ==='
select to_char(create_time,'HH24:MI:SS') t,
       length(details::jsonb->'chat_step'->'message_list'->0->>'content') as system_prompt_chars,
       jsonb_array_length(details::jsonb->'chat_step'->'message_list') as msg_count,
       message_tokens,
       answer_tokens,
       round(run_time::numeric,1) as rt_s
from application_chat_record
where create_time::date = current_date
order by create_time;
\echo '=== 昨天 23:22 那条（无工具）对比 ==='
select to_char(create_time,'MM-DD HH24:MI') t,
       length(details::jsonb->'chat_step'->'message_list'->0->>'content') as system_prompt_chars,
       jsonb_array_length(details::jsonb->'chat_step'->'message_list') as msg_count,
       message_tokens, answer_tokens
from application_chat_record
where create_time::date = '2026-11-15'
order by create_time;
