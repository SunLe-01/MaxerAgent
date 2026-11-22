# 《Agent 设计范式》考点 × 本项目实现对照

> 对照文章：小林面试笔记 · 第 4 题「了解哪些其他的 Agent 设计范式？Agent 和 Workflow 的区别」
> 对照对象：`E:\Desktop\oncall-agent`（MaxKB v2.10.8-lts，容器内 `/opt/maxkb-app` 实跑）
> 验证方式：源码走查 + `deepagents 0.6.11` 包级核查 + 真实对话实测（2026-11-16 14:54）

---

## 0. 结论速览

| 范式 | 项目里有吗 | 证据强度 | 一句话 |
|---|---|---|---|
| **Workflow vs Agent** | ✅✅ 两者都有 | 强 | 你自己刚搭的那个工作流 vs SIMPLE 应用，就是活对比 |
| **ReAct** | ✅ **隐式实现** | 中强 | 工具循环 + 推理过程，但没有显式 Thought 提示词 |
| **Plan-and-Execute** | ⚠️ **能力具备、未启用** | 中 | `write_todos` 工具随时可用，实测模型没调用 |
| **Reflection / Reflexion** | ❌ **库里有、项目关了** | 强 | 库自带 `RubricMiddleware`，MaxKB 没传 `middleware=` |
| **Agentic Workflow** | ✅✅ 就是本项目形态 | 强 | 固定流水线 + 末端嵌一个 Agent |
| **多 Agent 协作** | ✅ 有（Workflow 层） | 中 | 「智能体节点」把另一个应用当工具调 |

> 面试关键：**别把「库支持」说成「我用了」**。`write_todos` 和 `RubricMiddleware` 都存在，但项目没启用——这个区别面试官一追问就露。

---

## 1. Workflow vs Agent：你有现成的对照组 ★

这是本章核心，而你手上正好有两个可以**并排演示**的应用。

### 同一个问题，两种范式

问题：`成都 2 晚 650，P4，3 天能报多少`

| | SIMPLE 应用（Agent） | WORK_FLOW 应用（Workflow） |
|---|---|---|
| 应用名 | 差旅制度答疑（测试） | 差旅工作流实验 |
| 决策者 | LLM 自己决定调不调工具 | 代码判断，判断器决定 |
| 实测路径 | `ls → ls → read_file → main × 4` | 参数提取 → 检索 → 判断器 → 工具 → AI 对话 |
| 工具失败时 | **自己把 `P4` 改成 `P4-P5` 重试** | **直接报错终止** |
| 确定性 | 低（两次跑路径可能不同） | 高（同一输入必走同一条边） |

**面试话术**：

> 这两个应用我都搭过，同一个问题差别非常直观。
> Agent 那个，用户说 P4，模型先传 P4 报错，它自己读错误信息改成 P4-P5 又调了一次，成功了——这就是 LLM 在驱动。
> Workflow 那个，同样传 P4 就直接抛异常，因为没有人会去重试，控制流是我写死的。
> **这就是「谁决定下一步」最直接的体感。**

---

## 2. ReAct：项目里是「隐式 ReAct」

### 文章的定义

Thought → Action → Observation 循环，直到 LLM 判断可以给最终答案。

### 项目实现

`apps/application/flow/tools.py` 里走的是 LangGraph 的 agent 循环：

```python
agent = create_deep_agent(
    model=chat_model,
    tools=tools,                    # MCP 工具
    skills=["/skills"],             # 技能目录
    checkpointer=MemorySaver(),
)
recursion_limit = int(CONFIG.get("LANGCHAIN_GRAPH_RECURSION_LIMIT", "100"))
response = agent.astream({...}, config={"recursion_limit": recursion_limit, ...})
```

三轮要素在项目里的对应：

| ReAct 环节 | 项目里的体现 | 证据 |
|---|---|---|
| **Thought** | 模型的推理过程（`reasoning_content`） | 代码里有 `Reasoning` 类专门处理 think 标签的起止 |
| **Action** | `tool_calls` | `<tool_calls_render>{"title":"main","input":...}` |
| **Observation** | 工具返回值回灌 | `<tool_calls_render>{...,"output":"{\"result\":...}"}` |
| **停止** | LLM 不再调工具，或撞 `recursion_limit=100` | `config` 里显式传了上限 |

**实测的一次 ReAct 循环**（14:54:49 这次）：

```
1. ls          → ['/skills/']
2. ls          → ['/skills']            （Observation 后调整了参数）
3. read_file   → SKILL.md 内容
4. main × 4    → 试算器调用
```

注意第 1、2 步：**第一次 `ls` 得到 `/skills/`，第二次才带对路径 `/skills`** —— 这就是 Observation 影响下一轮 Action 的直接证据。

### 但要诚实：这不是「教科书 ReAct」

| 差异 | 说明 |
|---|---|
| 没有显式 Thought 提示词 | 项目里 grep `Thought` / `ReAct` / `Action:` → **0 命中**，没有「请先输出 Thought 再 Action」的 prompt |
| 推理过程未必暴露 | `deepseek-v4.1-flash` 的 `reasoning_content` 在本项目里没开启输出（`answer_text` 里 `think`/`reasoning` 都是 `false`） |
| 依赖模型原生 tool-calling | 是 function calling 循环，不是文本解析 `Action: xxx` |

**面试话术（这样说不虚）**：

> 我们用的是 function-calling 的原生循环，本质是 ReAct 的变体：模型输出 tool_call，我们执行后把结果回灌，它再决定下一步。
> 区别是我没有强制它先写 Thought，所以推理过程不一定可见——这是可观测性上的一个缺口，如果要做调试，我会把 reasoning 字段透出来。

---

## 3. Plan-and-Execute：能力在，但没启用

### 关键发现

`deepagents 0.6.11` 的包描述：

> *"General purpose 'deep agent' with **sub-agent spawning, todo list capabilities**, and mock file system."*

`create_deep_agent` 的默认工具清单（源码注释）：

```
- `write_todos`: manage a todo list
- `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`
- `execute`: run shell commands
- `task`: call subagents
```

而且主 agent 的中间件栈是**无条件**装配的：

```python
# deepagents/graph.py
deepagent_middleware = [
    TodoListMiddleware(),      # ← 没有 if，恒定加入
]
```

### 但实测没被使用

14:54 那次调用序列：`ls, ls, read_file, main, main, main, main` —— **没有 `write_todos`，也没有 `task`**。

原因很直接：`write_todos` 是**模型自主决定**要不要用的工具。这个任务只有 4 步、且都在一个 prompt 里说清了，模型判断不需要列计划。

### 怎么讲才准确

> Plan-and-Execute 的**能力是具备的**：底层 deepagents 默认给 agent 装了 `write_todos` 待办清单工具和 `task` 子代理工具。
> 但我实测过，对于我这种单轮 4~5 步的任务，模型不会主动用——它觉得直接干就行。
> **要真正用上，得在提示词里明确要求「先列计划再执行」**，否则这个范式就是闲置的。

> 💡 这句话说出来，比说「我们实现了 Plan-and-Execute」有说服力得多。

---

## 4. Reflection：库里有完整实现，项目关着 ★

### 这是本章最容易答错的一题

文章强调：**Reflection 是正式的运行时机制，不是调试工具**，代价是 token 和延迟。

### 库里确实有

`deepagents/middleware/rubric.py` 就是标准 Reflection：

```python
"""Rubric middleware for self-evaluated agent iteration.

Each time the agent would otherwise finish — i.e. the model returns a
response with no further tool calls — the middleware invokes a separate
grader sub-agent against the transcript. If the grader returns
`needs_revision`, its feedback is injected as a `HumanMessage` and the
agent loop resumes. Grading repeats until the grader returns `satisfied`
or `failed`, or `max_iterations` is reached.
"""
```

这几乎逐字对应文章说的机制：
- `satisfied` → 通过，结束
- `needs_revision` → **反馈注入 + 继续循环**（就是 Reflexion 的「错题本」）
- `max_iterations` → 上限兜底

### 但项目没有启用

```python
# 项目侧调用（apps/application/flow/tools.py）
agent = create_deep_agent(
    model=chat_model,
    backend=SandboxShellBackend(...),
    skills=["/skills"],
    tools=tools,
    system_prompt=system_prompt,
    interrupt_on={...},
    checkpointer=checkpointer,
)       # ← 没有传 middleware=[RubricMiddleware(...)]
```

全项目 grep `RubricMiddleware` / `rubric` → **0 命中**。

另外项目自身并没有「评估-重写」节点：`flow/step_node/**` 里 `评估|评审|critique|evaluator` 也是 **0 命中**。

### 怎么讲（诚实 + 有洞察）

> Reflection 我项目里**没用**，但我知道它在这儿是现成的：deepagents 自带 `RubricMiddleware`，机制就是 grader 判 `needs_revision` 就把反馈作为 HumanMessage 塞回去重跑，还有 `max_iterations` 上限。
> 我没开是因为它每轮多一次甚至多次 LLM 调用——我用 DeepSeek 时一次问答已经要 8k~10k prompt token，再加一层评审，延迟和成本都翻倍。
> **这是个明确的取舍，不是不知道。**

> 这一段能同时证明：①你懂范式 ②你懂原理 ③你知道代价 ④你做了权衡。比「我们实现了」强得多。

---

## 5. Agentic Workflow：本项目的真实形态

### 结构

```
SIMPLE 应用（chat_pipeline）
├─ BaseResetProblemStep      固定：问题改写（可选）
├─ BaseSearchDatasetStep     固定：向量检索
├─ BaseGenerateHumanMessage  固定：拼 prompt
└─ BaseChatStep              ★ Agent：create_deep_agent 自己调工具
```

### 对照文章结论

文章说生产主流是「Workflow 框骨架 + 关键节点嵌 Agent」，并引用 Anthropic 的原则：

> **能用 Workflow 解决的问题，就不要用 Agent。**

你的项目恰好是这个原则的实证：

| 环节 | 用了什么 | 为什么 |
|---|---|---|
| 检索 | 固定 Workflow 节点 | 流程确定，不需要决策 |
| 拼 prompt | 固定代码 | 完全确定性 |
| 工具调用 | **Agent** | 需要判断该不该调、调几轮 |

**面试话术**：

> 我这条链路就是 Agentic Workflow：前面检索、拼 prompt 全是写死的，只有最后一步是 Agent。
> 而且我做过一个对照实验——同一个问题，纯 Workflow 版本（我自己搭的那个）遇到 `P4` 就报错停了，Agent 版本自己纠正重试成功了。
> **所以我现在的判断是：能用 Workflow 就用 Workflow，只在真正需要灵活判断的那一步放 Agent。**

---

## 6. 多 Agent 协作：项目里是「应用即工具」

文章开头提到面试官说「多 Agent 协作是架构模式，不是设计范式」——这本身也是个考点。

项目里的多 Agent 能力：

| 机制 | 位置 | 说明 |
|---|---|---|
| **智能体节点** | `application_node` | 把另一个已发布的应用当成工作流里的一个节点 |
| **MCP 互调** | `chat/views/mcp.py` | 应用可暴露成 MCP 工具，被别的 Agent 调用 |
| **子代理（未启用）** | `deepagents` 的 `task` 工具 | 默认附带 general-purpose subagent，实测未触发 |

**面试话术**：

> 多 Agent 在我们项目里不是靠 prompt 编排的，是**协议层**的：一个应用可以发布成 MCP 工具，另一个应用通过「智能体节点」把它当工具调。
> 这属于架构层面，确实不是设计范式。

---

## 7. 一句话应对「这三种范式怎么选」

文章给的判断维度是**任务复杂度**和**质量要求**：

| 场景 | 选什么 | 项目里的映射 |
|---|---|---|
| 步骤少、彼此独立 | ReAct | SIMPLE 应用，实测 4 步搞定 |
| 步骤多、有依赖 | Plan-and-Execute | 工具链具备（`write_todos`），需提示词驱动 |
| 质量要求极高、允许慢 | 叠 Reflection | `RubricMiddleware` 可用，当前关闭 |
| 流程固定 | 纯 Workflow | 你搭的那个工作流 |

---

## 8. 面试可能的追问（提前准备）

### Q1「你说 ReAct 是隐式的，那和真 ReAct 差在哪？」
> 差在**Thought 是否被强制显式化**。
> 教科书 ReAct 要求模型先写推理再行动，好处是能看它在哪想歪了；我用的是 function calling，模型可能直接吐 tool_call，推理过程不一定落到文本里。
> 代价是可观测性：出了问题我只能看到「它调了什么」，看不到「它为什么这么调」。

### Q2「Plan-and-Execute 你没用，那什么情况下会用？」
> 任务步骤超过 8~10 步、或者步骤之间有依赖时。
> 我实测过，4 步的任务模型不会主动列 todo；但如果是「审一张报销单里的 20 条明细」这种，我会在提示词里强制它先列计划，否则容易中间丢目标。

### Q3「Reflection 能提升质量，你为什么不做？」
> 成本。我测过单次问答 prompt token 在 8,430~10,596 之间，加一轮 grader 就翻倍。
> 而且我这个场景是「查制度 + 算钱」，答案对错有客观标准（工具返回值），不需要 LLM 再评一遍——**用确定性校验比用 Reflection 更便宜也更准**。
> 真需要 Reflection 的场景是写文案、写代码这种「没有唯一正确答案」的。

> 💡 这个回答把「为什么不用」讲成了「什么时候该用」，是加分项。

### Q4「Workflow 和 Agent 到底怎么选？」
> 从确定性需求出发：要我保证每次都给同一个答案、且能定位出错节点 → Workflow。
> 要我处理我没预料到的输入 → Agent。
> 我实际的做法是**先写 Workflow，只有发现某个节点确实写不死了，才把那个节点升级成 Agent**——这也符合 Anthropic 的建议。

---

## 9. 速记卡

```
ReAct            → ✅ 隐式（function calling 循环 + 工具结果回灌）
                   证据：ls→ls→read_file→main×4，Observation 影响下一轮
                   短板：Thought 未强制显式，推理不可见

Plan-and-Execute → ⚠️ 能力在（deepagents 默认装 write_todos + task），
                   实测未触发；要提示词驱动才会用

Reflection       → ❌ 库里有 RubricMiddleware（needs_revision→反馈注入→重跑），
                   项目未传 middleware=，全项目 0 命中
                   原因：token 翻倍，且我有工具返回的确定性校验

Agentic Workflow → ✅ 本项目形态：检索/拼prompt写死，末端 BaseChatStep 是 Agent

多Agent          → ✅ 应用即工具（智能体节点 + MCP），属架构非范式

对照组（最值钱）→ 同一问题：Agent 自己把 P4 改成 P4-P5 重试成功；
                   我搭的 Workflow 直接报错终止
```

---

## 附：核查命令

```powershell
# ReAct 痕迹
docker exec maxkb sh -c "grep -rln 'Thought\|ReAct\|Action:' /opt/maxkb-app/apps --include=*.py"

# Plan-and-Execute 是否默认装配
docker exec maxkb sh -c "grep -n 'TodoListMiddleware' /opt/py3/lib/python3.11/site-packages/deepagents/graph.py"

# Reflection 是否启用（应为空）
docker exec maxkb sh -c "grep -rn 'RubricMiddleware' /opt/maxkb-app/apps --include=*.py"

# 默认工具清单
docker exec maxkb sh -c "sed -n '261,270p' /opt/py3/lib/python3.11/site-packages/deepagents/graph.py"
```
