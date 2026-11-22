\pset pager off
\echo '=== 最近两次执行：走了哪些节点 ==='
select to_char(create_time,'HH24:MI:SS') as t,
       left(problem_text, 24) as q,
       (select string_agg(distinct d->>'name', ' | ')
          from jsonb_each(details::jsonb) as e(k, d)) as visited_nodes,
       left(answer_text, 50) as ans
from application_chat_record
where chat_id in (select id from application_chat
                  where application_id = (select id from application where name='差旅工作流实验'))
order by create_time desc limit 4;

\echo '=== 工具节点的执行结果 ==='
select jsonb_pretty(v)
from application_chat_record r,
     jsonb_each(r.details::jsonb) as e(k, v)
where r.chat_id in (select id from application_chat
                    where application_id = (select id from application where name='差旅工作流实验'))
  and v->>'type' = 'tool-lib-node'
order by r.create_time desc limit 1;
