\pset pager off
\echo '=== 最近 3 条记录的耗时与 token ==='
select to_char(create_time,'HH24:MI:SS') as t,
       round(run_time::numeric,2) as run_time_s,
       message_tokens, answer_tokens,
       (details::jsonb->'chat_step'->>'run_time')::numeric as step_run_time,
       length(answer_text) as ans_len,
       position('<tool_calls_render>' in answer_text) > 0 as has_tool
from application_chat_record
order by create_time desc limit 3;
\echo '=== 段落/向量/问题统计（演示可引用）==='
select (select count(*) from paragraph) as paragraphs,
       (select count(*) from embedding where source_type='1') as para_vectors,
       (select count(*) from problem) as generated_problems,
       (select count(*) from tool) as tools,
       (select count(*) from application_version) as app_versions;
