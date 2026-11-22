# MaxerAgent · 差旅制度答疑智能体

基于 [MaxKB](https://github.com/1Panel-dev/MaxKB) v2.10.8-lts 搭建的垂直场景 Agent 实践项目：
把一份《差旅与费用报销管理办法》做成知识库，并配上**计算工具**和**审核技能**，实现「查规定 / 算金额 / 审单据」三类问答。

本项目不是框架源码，而是**完整的工程实践记录**：配置、工作流、踩坑、实测数据，以及对照 Agent / RAG 面试考点的逐条分析。

---

## 一、它解决什么问题

差旅报销场景有三类典型提问，需要三种完全不同的处理方式：

| 提问类型 | 例子 | 处理方式 |
|---|---|---|
| 查规定 | 「二类城市 P4 的住宿上限是多少？」 | 知识库检索 → 引用条款作答 |
| 算金额 | 「成都 2 晚 650，P4，3 天能报多少？」 | **调用工具**（禁止模型心算） |
| 审单据 | 「帮我审核这笔报销：住宿两晚 1300，拖到 12/20 才交…」 | **调用技能**（读 SKILL.md 按流程审） |

难点在于：算钱类问题**在制度文档里根本没有对应段落**，纯 RAG 检索必然召回失败——这就是为什么要引入工具，以及为什么要在提示词里做三分支路由。

---

## 二、架构

```
                    用户提问
                       │
        ┌──────────────┴──────────────┐
        │                             │
   SIMPLE 应用                   WORK_FLOW 应用
  （Agent 驱动）                 （Workflow 驱动）
        │                             │
  chat_pipeline:              开始 → 参数提取 → 知识库检索
  ├ 问题优化（可选）                    ↓
  ├ 向量检索                      判断器 ──IF(参数齐全)──→ 差旅报销试算器 → AI 对话
  ├ 拼 prompt                          └──ELSE(纯问答)──────────────→ AI 对话
  └ Agent 循环（自主决定调不调工具）
        │
   ┌────┴────┐
  工具        技能
  试算器      SKILL.md + audit.py
```

**两个应用刻意并存，用来对照「谁做决策」：**

- **SIMPLE（Agent）**：`create_deep_agent` + MCP 工具，模型自己决定调不调、调几次。
  同一句「P4」，工具报错后**模型会自己改成 P4-P5 重试**。
- **WORK_FLOW（Workflow）**：控制流写死在画布上，判断器决定走哪条边。
  同样传「P4」，**直接抛异常终止**，没有任何重试。

这个对比是本项目最核心的演示点。

---

## 三、技术栈

| 层 | 选型 |
|---|---|
| 底座 | MaxKB v2.10.8-lts（Django 5.2 + LangChain/LangGraph + Vue 3） |
| 数据库 | PostgreSQL 17 + pgvector 0.8.6 |
| 缓存/队列 | Redis + Celery |
| 大模型 | DeepSeek-Flash（OpenAI 兼容协议，走中转网关） |
| Embedding | 阿里百炼 `qwen3.7-text-embedding`（1024 维） |
| 部署 | Docker（单容器，`1panel/maxkb`） |
| 工具运行时 | 每个 Python 工具被编译成 **stdio MCP server**，由 Agent 消费 |

---

## 四、目录结构

```
.
├── README.md
├── .gitignore
├── patches/
│   └── 0001-hide-topbar-buttons.patch   # 对 MaxKB 前端的一处改动（见下）
│
├── 项目分析报告.md                       # 全项目体检：21 项问题 + 建议
├── 面试对照-Workflow-Agent-Tools.md      # 对照「Workflow/Agent/Tools」考点
├── 面试对照-Agent设计范式.md             # 对照 ReAct / Plan-and-Execute / Reflection
├── 面试对照-复杂任务拆分.md              # 对照「任务拆分与并行」
├── 面试讲稿-Workflow-Agent-Tools.md      # 可直接照着练的面试讲稿
│
├── output/                              # 业务资产与实测快照
│   ├── 星澜科技-差旅与费用报销管理办法-V2.1.docx / .md
│   ├── travel-expense-audit.zip          # 审核技能包（SKILL.md + audit.py）
│   ├── wf_dump.json                      # 工作流完整配置
│   └── chat_*.txt                        # 对话流快照（含工具调用轨迹）
│
└── *.py                                 # 配置/探针/修复脚本（见下方说明）
```

**关于 `output/` 里的制度文档**：由 `make_travel_policy.py` 用 python-docx **程序化生成**，
「星澜信息技术有限公司」是虚构主体，住宿/伙食/境外补贴数值均为演示数据，**不可当真实制度使用**。

### 脚本分类

| 前缀 | 用途 |
|---|---|
| `make_travel_policy.py` / `docx_to_md.py` / `verify_docx.py` | 生成制度文档并校验 |
| `setup_agent_tools.py` / `attach_skill.py` / `enable_tools.py` | 创建工具、挂技能到应用 |
| `configure_models.ps1` | 批量配置模型（百炼系列 + DeepSeek） |
| `fix_workflow*.py` | 修复工作流的四个连续问题（见「踩坑记录」） |
| `probe_*.py` | 探针：检索、分片、向量库、MCP、工具调用轨迹 |
| `verify_startup.py` | 启动后端到端验证 |
| `test_chat*.py` / `test_skill.py` | 对话链路测试

---

## 五、快速开始

### 1. 启动容器

```bash
docker run -d --name maxkb --restart always \
  -p 18080:8080 \
  -v "E:/Desktop/maxkb:/opt/maxkb" \
  1panel/maxkb
```

> **端口说明**：默认应该用 8080。但 Windows 的 Hyper-V/WinNAT 动态端口预留区间
> （`netsh int ipv4 show excludedportrange protocol=tcp` 可见 `7998-8097`）会占用 8080，
> 导致 Docker 报 `bind: An attempt was made to access a socket in a way forbidden by its access permissions`。
> 解决办法二选一：换端口（如上），或管理员执行 `net stop winnat` → `netsh int ipv4 set dynamicport tcp start=20000 num=10000` → `net start winnat`。

访问 `http://127.0.0.1:18080/admin`。

### 2. 配置环境变量

脚本里的凭据已全部改为环境变量，**运行前必须设置**：

```powershell
$env:MAXKB_BASE_URL  = "http://127.0.0.1:18080"   # 可选，脚本内默认值
$env:MAXKB_PASSWORD  = "你的管理员口令"            # 必填
$env:MAXKB_DASHSCOPE_KEY = "sk-..."                # 仅 configure_models.ps1 需要
$env:MAXKB_RELAY_KEY     = "..."                   # 仅 configure_models.ps1 需要
```

### 3. 验证

```powershell
python verify_startup.py
```

预期输出：两条问答都返回 `[OK]`，且第二条的工具节点入参为
`{"city":"成都","days":3,"level":"P4-P5","nights":2,"hotel_price":650.0}`、返回 `1340`。

---

## 六、实测数据

同一应用下的三问（2026-11-16 实测，正式对话链路，已落库）：

| 问法 | 首字时延 | 总时延 | 工具调用 | 回答长度 | prompt token |
|---|---|---|---|---|---|
| 查规定（二类城市 P4 住宿上限） | 5.68s | **6.96s** | 0 次 | 135 字 | 8,430 |
| 算金额（成都 2 晚 650） | 3.57s | **24.13s** | 2 次 | 1,492 字 | 9,572 |
| 审单据（杭州报销单） | 6.96s | **66.41s** | 2 次 | 3,932 字 | 10,596 |

**这组数据的意义**：延迟和 token 随工具轮次线性增长，不是模型变慢。
优化方向应是**减少不必要的工具轮次**，而不是换更快的模型。

工具实际返回（数据库证据）：

```json
{"city_tier":"二类","lodging_cap_per_night":550,"lodging_reimbursable":1100,
 "lodging_over":200,"meal_allowance_total":240,"travel_total_reimbursable":1340}
```

---

## 七、设计决策

**1. 三分支路由提示词**
`model_setting.system` 里强制三条路径：查规定走知识库并标注条款；算钱/审单必须调工具、禁止心算；
两者都不适用就固定回「知识库中未找到相关条款，建议咨询行政人事部」。
最后这条**拒答出口**是刻意加的——宁可说不知道，也不让模型编。

**2. 宁可维护双份标准，也不让模型算钱**
住宿上限、伙食标准同时存在于制度文档和工具代码中，是刻意接受的双份事实源。
因为让 LLM 心算金额的错率远高于维护两份的成本。

**3. 检索参数**
`top_n=3`、`similarity` 从 0.6 下调到 **0.35**（原因见踩坑记录）。
已配置 `百炼-Rerank` 但未启用——这是已知的优化空间。

---

## 八、踩坑记录（最有价值的部分）

### 坑 1：Agent 的「不确定性」其实是版本切换

同一问题（「成都 2 晚 650…」）多次表现不一致：有时回「未找到条款」，有时正确调工具算出 1,340。
第一反应是「Agent 随机性」，但查落库 token 后发现：

| 时间 | 服务版本 | message_tokens | 调工具 |
|---|---|---|---|
| 11-15 18:48–23:22（5 次） | 17:50 版，**无工具** | 1,097 | ❌ |
| 11-15 23:28 起 | 23:26 版，**有工具** | 10,697 | ✅ |

真相是 23:26 重新发布过一次应用，之前那版根本没挂工具。
**教训：排查顺序应是「先查版本/配置，再怀疑模型」。**

### 坑 2：工具入参在 UI 上「选变量」，底层却要求模板字符串

MaxKB 的工具节点 `input_field_list` 里，`source` 取自**工具定义**（恒为 `custom`），
节点上设的 `source: reference` 会被覆盖，因此永远走「模板字符串」分支：

```python
{ 'value': get_field_value(节点入参, name, required), **工具定义字段 }
```

正确写法是 `"{{参数提取.city}}"`，**不是** `["节点ID","city"]` 数组。

### 坑 3：相似度 0.6 让口语化问题永远召回失败

「成都 2 晚 650，P4，3 天能报多少」与制度原文「第十条 住宿标准表 二类城市 P4—P5 550 元/晚」
语义距离过远，`paragraph_list` 直接返回 `[]`，判断器永远走 ELSE。
降到 0.35 后，「二类城市住宿上限」的命中相似度是 0.778。

> 复盘：降阈值是**用召回精度换命中率**。更正确的做法是启用 **Query Rewrite（问题优化）**
> 或 **HyDE**，先把口语问题改写成条款式表述，再调阈值。

### 坑 4：判断器判断对象的选错

最初判断「检索是否命中」，导致纯查规定类问题也被卷进工具分支。
应改为判断「参数是否齐全」（`nights` / `hotel_price` 是否非空）——算钱靠工具，不靠检索。

### 坑 5：AI 对话节点默认 AND 依赖，导致答案为空

`AI 对话` 有两条入边（工具 / 判断器 ELSE），但节点 `condition` 默认 `AND`，
要求**所有上游都执行过**。走 ELSE 时工具没执行 → 节点被整个跳过 → 答案是空字符串。

```python
if next_node.properties.get('condition', "AND") == 'AND':
    if self.dependent_node_been_executed(edge.targetNodeId): ...   # 依赖校验
else:
    node_list.append(...)                                          # OR 直接放行
```

把 `condition` 改成 `OR` 解决。

---

## 九、面试笔记索引

| 文档 | 覆盖考点 |
|---|---|
| [项目分析报告](项目分析报告.md) | 全项目体检：架构、数据、21 项风险与建议 |
| [Workflow / Agent / Tools](面试对照-Workflow-Agent-Tools.md) | 三层粒度、「谁做决策」、MCP 三重身份、工具设计四原则 |
| [Agent 设计范式](面试对照-Agent设计范式.md) | ReAct（隐式）、Plan-and-Execute（能力在未启用）、Reflection（库有未开） |
| [复杂任务拆分](面试对照-复杂任务拆分.md) | 静态/动态拆分、DAG 依赖分析、并行执行、自适应拆分缺失 |
| [面试讲稿](面试讲稿-Workflow-Agent-Tools.md) | 分层讲法、必讲的坑、现场演示脚本、追问防御表 |

---

## 十、已知不足

- **Query Rewrite 未启用**：SIMPLE 应用的 `problem_optimization=false`，工作流也没有 `问题优化` 节点。
  HyDE / Step-back / 多 Query 扩展均未实现。
- **无 Reflection**：底层 `deepagents` 自带 `RubricMiddleware`，但未传 `middleware=` 参数。
- **无自适应拆分 / 显式 Replan**：工作流是静态画布，运行时不会生成新节点。
- **段落向量有重复**：29 个段落对应 42 条 active 向量（最多一段 4 条），会浪费 `top_n` 配额。
- **备份缺失**：数据库在 `E:/Desktop/maxkb/data`，docx 与技能包以 PostgreSQL large object 存库，
  不做备份则一处丢失全丢。

---

## 十一、许可证与致谢

- 本仓库**不包含** MaxKB 源码。MaxKB 是 [1Panel-dev/MaxKB](https://github.com/1Panel-dev/MaxKB)，
  采用 **GPL-3.0** 许可。部署与二次开发请遵守其许可条款。
- `patches/0001-hide-topbar-buttons.patch` 记录了对 MaxKB 前端的一处改动
  （移除顶栏的升级/GitHub/手册/论坛按钮），需在 MaxKB 源码目录执行
  `git apply ../patches/0001-hide-topbar-buttons.patch` 应用。
- 本项目内的制度文档为虚构演示数据，「星澜信息技术有限公司」不对应任何真实实体。
