\pset pager off
\echo '=== users ==='
select username, nick_name, role, is_active, create_time from "user" order by create_time;
\echo '=== model credential keys (masked) ==='
select name, model_type, model_name, provider,
       jsonb_object_keys(credential::jsonb) as cred_key
from model order by model_type;
\echo '=== LLM base_url ==='
select name, credential::jsonb->>'base_url' as base_url,
       length(credential::jsonb->>'api_key') as key_len
from model where model_type in ('LLM','EMBEDDING','RERANKER');
\echo '=== migrations (last 10) ==='
select app, name, applied from django_migrations order by applied desc limit 10;
\echo '=== knowledge_action ==='
select * from knowledge_action;
\echo '=== problem count ==='
select count(*) from problem;
\echo '=== paragraph sample ==='
select left(content, 120) as content, status, is_active from paragraph order by create_time limit 5;
