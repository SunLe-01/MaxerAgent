\pset pager off
\echo '=== 现有应用类型 ==='
select name, type, is_publish, to_char(create_time,'MM-DD HH24:MI') t from application;
\echo '=== 工作流类表 ==='
select 'tool_workflow' t, count(*) from tool_workflow
union all select 'knowledge_workflow', count(*) from knowledge_workflow
union all select 'application_version', count(*) from application_version;
\echo '=== 可复用资源 ==='
select 'knowledge' t, name, id::text from knowledge
union all select 'model', name, id::text from model where model_type='LLM'
union all select 'tool', name||' ('||tool_type||')', id::text from tool where tool_type in ('CUSTOM','SKILL');
