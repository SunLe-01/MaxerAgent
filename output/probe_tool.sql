\pset pager off
\echo '=== custom/skill tool metadata ==='
select name, "desc", tool_type, input_field_list::text as params
from tool where tool_type in ('CUSTOM','SKILL');
