\pset pager off
\echo '=== 两个发布版本的关键差异 ==='
select to_char(create_time,'MM-DD HH24:MI') as published_at,
       length(model_setting::jsonb->>'system') as prompt_chars,
       tool_ids::text as tool_ids,
       skill_tool_ids::text as skill_ids,
       jsonb_array_length(coalesce(knowledge_ids,'[]'::jsonb)) as kb_count
from application_version
order by create_time;
\echo '=== 每条对话发生在哪个版本之后 ==='
select to_char(r.create_time,'MM-DD HH24:MI') as chat_at,
       r.message_tokens,
       (select to_char(v.create_time,'MM-DD HH24:MI')
          from application_version v
         where v.application_id = '01a1de97-cfe1-7f23-baa8-9caf5bdc25a8'
           and v.create_time <= r.create_time
         order by v.create_time desc limit 1) as served_by_version,
       (position('<tool_calls_render>' in r.answer_text) > 0) as called_tool
from application_chat_record r
order by r.create_time;
