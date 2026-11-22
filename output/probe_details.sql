\pset pager off
\echo '=== 14:25 那次执行的 details（命中 0 条的验证）==='
select jsonb_pretty(details::jsonb)
from application_chat_record
where to_char(create_time,'HH24:MI') = '14:25';

\echo '=== 14:01 那次执行的 details ==='
select jsonb_pretty(details::jsonb)
from application_chat_record
where to_char(create_time,'HH24:MI') = '14:01';
