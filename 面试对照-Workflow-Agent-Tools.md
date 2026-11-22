# 《Workflow / Agent / Tools》考点 × 本项目实现对照

> 对照文章：小林面试笔记 · 第 3 题「Workflow，Agent，Tools 这三个的概念和区别」
> 对照对象：`E:\Desktop\oncall-agent`（MaxKB v2.10.8-lts + 「差旅制度答疑」智能体）
> 所有结论都核对过**容器内实际运行的代码**（`/opt/maxkb-app`），不是只看本地源码。

---

## 0. 一句话结论

这一章的 6 个核心考点，**项目覆盖了 5 个，而且每个都能指到具体文件和实测现象**；缺 1 个（Evaluator-Optimizer）。
更关键的是：**这个项目本身就是文章结论"Agentic Workflow 才是生产主流"的一个完整样本** —— 固定骨架 + 骨架里嵌一个会自己调工具的 Agent。

| # | 考点 | 项目覆盖 | 证据强度 |
|---|---|---|---|
| 1 | Tools = schema + 执行体，本身不决策 | ✅ 完整实现 | 代码 + 数据库元数据 |
| 2 | 工具设计四原则 | ✅ 三条做得好，**一条被违反** | 实测对话可复现 |
| 3 | MCP 是工具世界的 USB 接口 | ✅✅ 三重身份，超出文章深度 | 代码 + 端点 |
| 4 | Agent = LLM 自己决定循环 + 停止条件 | ✅ 完整实现 | 代码 + 实测不确定性 |
| 5 | Workflow = 开发者写死控制流 | ✅ 完整实现（平台级） | 代码，36 种节点 |
| 6 | Agentic Workflow = 骨架 + 灵活节点 | ✅ 本项目实际形态 | 运行时 pipeline |
| — | Evaluator-Optimizer | ❌ 缺失 | 全库 grep 0 命中 |

---

## 1. Tools：最小的能力积木

**考点原话**：Tool 是「按特定格式暴露给 LLM 的函数」，必须有 LLM 看得懂的 schema（名字、描述、参数类型）；工具本身没有任何决策能力。

**项目证据**：工具的定义和实现是**物理分离**的两列。

| 层 | 存储位置 | 内容 |
|---|---|---|
| 说明书 | `tool.desc` + `tool.input_field_list` | 描述 + 参数（name/type/is_required） |
| 执行体 | `tool.code` | 一段 Python 函数体 |

实际数据（`差旅报销试算器`）：

```
desc  : 根据城市、职级、住宿晚数、实际房价和出差天数，计算本次出差的住宿可报上限、
        伙食补贴、超标金额与合计可报金额。当用户问『我这次出差能报多少』
        『住宿超标多少』时调用。
params: city:string / level:string / nights:int / hotel_price:float / days:int  (全部 required)
```

**这两份东西最后怎么合到一起的**（`apps/common/utils/tool_code.py`）：
`get_tool_mcp_config()` 会把 `code` 用 AST 改写，生成一份 MCP server 代码，其中把 `desc` 原样塞进工具声明：

```python
functions.append(f"@mcp.tool(description='{escaped_desc}')\n{func_code}\n")
...
code_parts.append('\nmcp.run(transport="stdio")\n')
```

→ **`desc` 就是模型看到的 description，走的是同一条链，不存在"写了描述但没生效"的可能。**

`ToolType` 共 6 类：`INTERNAL` / `CUSTOM` / `SKILL` / `MCP` / `DATA_SOURCE` / `WORKFLOW` —— 对应文章说的"不同来源的工具统一管理"。

**面试话术**：
> 我们项目里"工具"就是一张表：一列放给模型看的说明书，一列放执行代码。发布时把执行代码编译成一个 stdio 的 MCP server，说明书变成 `@mcp.tool(description=...)`，模型只看到说明书，执行在独立进程里。

---

## 2. 工具设计四原则：三条做到了，一条被违反

文章给了四条：职责单一、描述精确、错误信息清晰、参数简洁。

| 原则 | 本项目 | 证据 |
|---|---|---|
| 职责单一 | ✅ | 试算器只算钱，审核技能只审单，互不掺和 |
| 描述精确 | ✅✅ | desc 里直接写触发语句「当用户问『我这次出差能报多少』时调用」，模型判断依据就是它 |
| 错误信息清晰 | ✅✅ | 见下方实测，**这是全项目最值得讲的一处** |
| 参数简洁 | ⚠️ **被违反** | 5 个参数全 required、无默认值；`level` 强制枚举 |

### 2.1 错误信息清晰 —— 有实测证据

工具对职级做了硬校验：

```python
if key not in lodging_cap:
    return {"error": "职级不支持：" + str(level) + "，请使用 P1-P3 / P4-P5 / M1-M2 / M3+"}
```

今天实测问「P4 能报多少」，模型先传 `level="P4"`，工具返回上面这句；**模型下一轮立刻改成 `P4-P5` 重调，成功拿到结果**：

```json
第 1 次调用 {"city":"成都","level":"P4",...}
         → {"result":{"error":"职级不支持：P4，请使用 P1-P3 / P4-P5 / M1-M2 / M3+"}}
第 2 次调用 {"city":"成都","level":"P4-P5",...}
         → {"result":{"query":{...},"lodging_cap_per_night":550,...}}
```

这就是文章说的「**前者能帮助 LLM 自己修正参数重试，后者它完全不知道该怎么处理**」的活例子。
反例写法是 `Error code 400`，模型只能瞎猜甚至放弃。

### 2.2 参数简洁 —— 反面教材

5 个参数全部必填、没有默认值，其中 `level` 还把用户口中的 `P4` 排除在外，导致**每一次 P4 提问都要多烧一轮 token**。
如果按文章原则改，应该：`level` 接受裸 `P4`（内部映射到 `P4-P5`），`days` 可由 `nights` 推默认值。

**面试话术**：
> 我们工具的错误文案是写给模型看的，不是写给人看的 —— 它会告诉模型"你该用哪个枚举值"，模型能自己纠正重试。
> 代价是我们参数设计不够收敛，一个枚举不匹配就让首轮必然失败，这是我看完这类文章后回头发现的真实改进点。

> 💡 面试里"我发现我们项目有个坑"比"我们完美实现了"可信得多，这条可以直接用。

---

## 3. MCP：文章点到，项目做深了

**考点原话**：MCP 把工具的注册、描述、调用做成一套标准协议，是工具世界的「USB 接口」。

项目里 MCP 不只是"支持"，而是**三重身份**：

| 身份 | 位置 | 说明 |
|---|---|---|
| **MCP Server**（对外暴露能力） | `apps/chat/views/mcp.py:29-35` | 处理 `initialize` / `tools/list` / `tools/call`，把整个应用变成一个可被别的 Agent 调用的工具 |
| **MCP Client**（消费外部能力） | `flow/step_node/mcp_node` + `langchain-mcp-adapters` | 接入外部 MCP server |
| **MCP 作为内部统一总线** | `tool_code.py:331` `get_tool_mcp_config` | **连本地 Python 工具都要包成 MCP server** 才能给 Agent 用 |

第三点是最值得讲的：一个 `@mcp.tool` 的 FastMCP 进程、`transport="stdio"`、`command=sys.executable`、代码用 `gzip+base64` 内联执行，还能 `setgid/setuid` 降权。
外部应用则是 `transport="streamable_http"` + Bearer key（`get_app_mcp_config`）。

**面试话术**：
> MCP 的价值在我们项目里体现得特别直接：本地函数、外部应用、第三方 MCP server 三种来源，进了 Agent 之后**都是同一个 `tools/list` + `tools/call` 接口**，上层完全不用区分来源。等于把"接一个工具写一套适配"变成了"接一次协议"。

---

## 4. Agent：LLM 自己决定循环，以及停止条件

**考点原话**：Agent 是 Thought → Action → Observation 的 `while True` 循环；生产环境必须有停止条件（LLM 判断完成 / 最大轮数 / token 预算 / 超时）。

**项目实现**（`apps/application/flow/tools.py`，容器同款）：

```python
agent = create_deep_agent(
    model=chat_model,
    tools=tools,                                  # 工具（来自 MCP）
    skills=["/skills"],                           # 技能目录
    interrupt_on={"write_file": False, ...},
    checkpointer=MemorySaver(),
)
recursion_limit = int(CONFIG.get("LANGCHAIN_GRAPH_RECURSION_LIMIT", "100"))
response = agent.astream({...}, config={"recursion_limit": recursion_limit, ...})
```

- 循环本体：LangGraph 的 `astream`，**跑几轮开发者不知道** —— 正是文章强调的那点。
- 停止条件：`recursion_limit` 默认 **100 轮**；工具异常不抛出而是回灌给模型（`tool.handle_tool_error = True`）。

项目里还有别的停止机制，可以一起答：

| 层 | 机制 | 默认值 |
|---|---|---|
| Agent | `LANGCHAIN_GRAPH_RECURSION_LIMIT` | 100 |
| Workflow | `WORKFLOW_LOOP_NODE_MAX_LOOP_COUNT`，超了抛 "Exceeding the maximum number of cycles" | 500 |
| 节点 | `is_interrupt_exec(current_node)` → 直接返回空后继节点 | — |

### 4.1 不确定性：项目里有现成的"事故现场"

文章说 Agent 同输入可能走不同路径。这个项目真的发生过：

| 时间 | 同一个问题「成都 2 晚 650，P4，3 天能报多少」 | 结果 |
|---|---|---|
| 11-15 18:48 / 18:49 / 20:13 / 23:22 | 没调工具 | 一律回「知识库中未找到相关条款」 |
| 11-15 23:28 与 11-16 12:54 | 调了工具（`main`） | 正确算出 1,340 元 |

而且即使调了工具，第一次也必然先撞 `P4` 枚举错误再自纠 —— **路径不一样，token 消耗和延迟都不一样，最终答案却一样**。
排查时只能靠落库的执行详情，这正是文章说的"必须记录每一步"。

### 4.2 可追溯性：执行日志落在哪

`application_chat_record.details` 是 JSON，按 step 存：

```json
{"chat_step": {"step_type":"chat_step","status":200,"run_time":35.83,
               "message_tokens":..., "answer_tokens":...,
               "message_list":[{"role":"system","content":"你是星澜…"}]}}
```

前端再把 `<tool_calls_render>{"title":"main","input":...,"output":...}</tool_calls_render>` 渲染出来 —— 入参、出参、耗时全在，出问题能回溯到"哪一步、传了什么、返回了什么"。

---

## 5. Workflow：控制流由代码写死

**考点原话**：Workflow 的节点可以是 LLM / Agent / Tools，关键在于「下一步去哪」由开发者决定；典型实现就是 if/elif + 固定顺序。

**项目实现**（`workflow_manage.py:377-387`，一段代码同时演示了两种编排模式）：

```python
node_list = self.get_next_node_list(current_node, result)
if len(node_list) == 1:
    self.run_chain_manage(node_list[0], None, language)          # 单后继 → 串行 = Prompt Chaining
elif len(node_list) > 1:
    result_list = [{'node': node, 'future': executor.submit(
        self.run_chain_manage, node, None, language)} for node in sorted_node_run_list]
    for r in result_list:
        self.future_list.append(r.get('future'))                 # 多后继 → 线程池并发 = Parallelization
```

- **分支判断**：`condition_node` + 21 种比较算子（equal / gt / contain / regex / wildcard / is_null…），边用 `{sourceNodeId}_{branch_id}_right` 锚点匹配，还支持 `AND` 汇聚（`dependent_node_been_executed`）。
- **LLM 只当分类器**：`intent_node` 的 prompt 明确要求返回 `{"classificationId": 0, "reason": ""}`，**分类结果只是 `branch_id`，走哪条边还是代码算的** —— 和文章客服系统的例子一模一样。
- **节点不必是 Agent**：36 种节点里，`condition`（纯代码）、`search_knowledge`（检索）、`variable_aggregation`（变量运算）、`form`（表单）都不是 Agent。正好回答文章开头的追问：「Workflow 里的节点必须是 Agent 吗？」——不是。

---

## 6. Agentic Workflow：项目本身就是答案

**考点原话**：生产主流不是纯 Agent，也不是纯 Workflow，而是「Workflow 固定骨架 + 关键节点嵌 Agent」。

本项目实际跑的那条链路（`apps/chat/serializers/chat.py:375-385`）就是教科书形态：

```python
if chat_info.application.problem_optimization:
    pipeline_manage_builder.append_step(BaseResetProblemStep)   # 可选：问题改写
pipeline_message = (pipeline_manage_builder
    .append_step(BaseSearchDatasetStep)        # 固定：检索知识库
    .append_step(BaseGenerateHumanMessageStep) # 固定：拼 prompt
    .append_step(BaseChatStep)                 # ★ 灵活：Agent 循环（可调工具）
    ...)
```

- **骨架是 Workflow**：顺序写死，检索→拼装→作答，可预测、好调试；
- **`BaseChatStep` 是 Agent**：内部 `create_deep_agent` + MCP 工具，自己决定调不调、调几次；
- **其余节点是 Tools**：检索、向量化、重排都是固定能力。

另外 ADVANCED 模式下还有 `application_node`（把另一个已发布应用当工具调），对应文章说的 **Orchestrator-Workers**。

**面试话术**：
> 我们线上那条链路就是 Agentic Workflow：前面的检索、拼 prompt 是写死的，保证可控和可观测；只有最后一步是 Agent，让它自己决定要不要调试算器、审核技能。出了事能定位到具体节点，同时又保留了处理意外输入的灵活性。

---

## 7. 项目里没有的：Evaluator-Optimizer

全库在 `flow/step_node/**` 里 grep `评估|评审|critique|evaluator` → **0 命中**。没有"生成 → 评审 → 重写"的闭环。

容易混淆的几个近似物，**都不是**这个模式：

| 机制 | 实际作用 | 为什么不是 Evaluator-Optimizer |
|---|---|---|
| `problem_optimization` | 把用户问题改写得更完整再检索 | 优化的是输入，不是输出 |
| `reranker` 节点 | 对召回的段落重新排序 | 评的是检索结果，不是生成答案 |
| `no_references_setting` | 检索不到时改走兜底话术 | 是降级策略，没有"重写再评" |

**如果被追问"你会怎么加"**（这就是加分项）：

> 用 `condition + ai_chat + loop` 三个节点就能搭：第一个 `ai_chat` 生成答案；第二个 `ai_chat` 当评审，按代码里定义好的打分维度输出 JSON（比如 `{"score": 7, "issues": [...]}`）；`condition` 判断分数是否达标，不达标就把 `issues` 带回第一个节点重写；外面套 `loop_node`，靠 `WORKFLOW_LOOP_NODE_MAX_LOOP_COUNT` 兜底防死循环。
> 关键点是**评分标准必须在代码里固定**，不能让评审模型自由发挥，否则评审本身也不可控。

---

## 8. 能直接背的 5 句「项目版」答案

1. **三者关系**：我们项目里三层同时存在——工具是被 MCP 包起来的函数，Agent 是拿着工具自己决定调几次的那一步，Workflow 是把检索、拼装、作答写死顺序的那条流水线。
2. **谁做决策**：工具没有决策能力，只负责被调用时执行；Agent 的循环次数连开发者都不知道，由 LangGraph 跑到模型自己停或撞上 `recursion_limit=100`；Workflow 的下一步由 `get_next_node_list()` 算出来，代码说了算。
3. **工具怎么设计**：我们的工具描述直接写触发语句，错误信息写成"请使用 P1-P3 / P4-P5"这种模型看得懂的格式，实测模型能自己纠正重试。
4. **为什么用 Agentic Workflow**：纯 Agent 路径不可控、成本不可控；纯 Workflow 遇到没穷举的输入就废。所以我们把检索固定、把决策留到最后一步。
5. **可观测性**：每个 step 的 message_list、tokens、run_time 都落库，前端把工具入参出参渲染出来，所以"路径不同"这件事是可排查的。

---

## 9. 面试官可能追问的 3 个坑（提前想好）

| 追问 | 别踩的坑 | 建议回答 |
|---|---|---|
| 「你怎么保证 Agent 不无限循环？」 | 只答"模型会自己停" | 四道闸：LLM 主动结束、`recursion_limit=100`、loop 节点 500 次上限、节点中断标记；实际工程还会加 token 预算和整体超时 |
| 「Workflow 节点里放 Agent，那还算 Workflow 吗？」 | 答"算/不算" | 算。判断标准是**控制流归谁**：外层骨架是代码写的，所以是 Workflow；被嵌进去那个节点内部循环归 LLM，所以节点是 Agent。两层互不冲突 |
| 「工具描述写得好不好，你怎么验证？」 | 空谈"写清楚就行" | 看调用准确率：同义问题各问一遍，统计该调没调、不该调乱调；我们那个 `P4` 枚举问题就是靠日志里的 tool_calls 发现的 |
