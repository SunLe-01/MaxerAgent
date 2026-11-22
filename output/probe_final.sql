\pset pager off
\echo '=== 最近 2 次：节点轨迹 ==='
select to_char(r.create_time,'HH24:MI:SS') as t,
       left(r.problem_text, 22) as q,
       (select string_agg(distinct v->>'name', ' -> ')
          from jsonb_each(r.details::jsonb) as e(k, v)) as visited
from application_chat_record r
where r.chat_id in (select id from application_chat
                    where application_id = (select id from application where name='差旅工作流实验'))
order by r.create_time desc limit 2;

\echo '=== 工具节点的入参与返回（关键证据）==='
select to_char(r.create_time,'HH24:MI:SS') as t,
       v->>'status' as status,
       v->'params' as params,
       v->'result' as result
from application_chat_record r,
     jsonb_each(r.details::jsonb) as e(k, v)
where r.chat_id in (select id from application_chat
                    where application_id = (select id from application where name='差旅工作流实验'))
  and v->>'type' = 'tool-lib-node'
order by r.create_time desc limit 2;
