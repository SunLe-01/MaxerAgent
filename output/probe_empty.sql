\pset pager off
\echo '=== 最近两次执行详情 ==='
select jsonb_pretty(details::jsonb)
from application_chat_record
where chat_id in (select id from application_chat
                  where application_id = (select id from application where name='差旅工作流实验'))
order by create_time desc limit 1;
