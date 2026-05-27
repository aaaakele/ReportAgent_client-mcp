# Mining Daily Agent - Full Project Plan

---

# 1. 项目概述

## 1.1 项目名称

**Mining Daily Agent**

基于 MCP（Model Context Protocol）的多工具矿业日报智能体。

---

## 1.2 项目目标

在 24 小时内构建一个完整可运行的 MCP Agent 系统，实现：

- 3 个独立 MCP Server
- 1 个 Agent Client
- Claude Desktop / Cursor 接入
- 权限控制机制
- 自动生成矿业日报
- Docker 一键启动

---

## 1.3 核心任务

用户输入：

```text
生成 Pilbara 锂矿今日简报
```

系统输出：

```markdown
# Pilbara Lithium Daily Report

## 今日重点
...

## 新闻摘要
...

## 储量变化
...

## 市场价格走势
...

## 风险提示
...

## 数据来源
...
```

---

# 2. 系统目标

系统需要具备以下能力：

## 2.1 新闻聚合

检索矿业新闻：

- Pilbara
- Lithium
- Australia mining
- WA policy

支持：

- 搜索新闻
- 抓取正文
- 自动摘要

---

## 2.2 PDF 储量解析

解析矿业报告：

- NI 43-101
- JORC
- 公司资源披露 PDF

提取：

- measured
- indicated
- inferred
- grade
- reserve change

---

## 2.3 行情分析

获取矿产品价格：

- Lithium carbonate
- Spodumene concentrate

分析：

- 当前价格
- 7日趋势
- 波动率

---

## 2.4 Agent 推理

自动完成：

1. 理解用户意图
2. 工具规划
3. 工具调用
4. 聚合结果
5. 报告生成

---

# 3. 技术栈

## 3.1 开发语言

Python 3.11+

---

## 3.2 MCP

FastMCP

---

## 3.3 Agent

LangGraph

---

## 3.4 LLM

支持配置：

- OpenAI
- DeepSeek
- Anthropic

---

## 3.5 PDF 解析

- pdfplumber
- pymupdf
- regex

---

## 3.6 新闻抓取

- trafilatura
- feedparser
- requests

---

## 3.7 模板渲染

Jinja2

---

## 3.8 缓存（可选）

- SQLite
- Redis

---

## 3.9 容器化

Docker + docker-compose

---

# 4. 系统架构

## 4.1 总体架构

```text
User
  ↓
Agent Client
  ↓
Planner
  ↓
Permission Validator
  ↓
Tool Router
  ├── mining-news-mcp
  ├── mineral-pdf-mcp
  └── lme-price-mcp
  ↓
Aggregator
  ↓
Report Generator
  ↓
Markdown Report
```

---

## 4.2 模块职责

### Agent Client

负责：

- 理解任务
- 制定执行计划
- 调度 MCP 工具
- 聚合结果

---

### MCP Server

负责：

- 提供标准化工具接口
- 独立执行任务
- 返回结构化结果

---

### Permission Layer

负责：

- 权限校验
- URL 白名单
- 文件沙箱
- 资源限制

---

# 5. 项目目录结构

```text
mining-daily-agent/
│
├── servers/
│   ├── mining_news/
│   │   ├── server.py
│   │   ├── tools.py
│   │   └── tests/
│   │
│   ├── mineral_pdf/
│   │   ├── server.py
│   │   ├── parser.py
│   │   └── tests/
│   │
│   └── lme_price/
│       ├── server.py
│       ├── provider.py
│       └── tests/
│
├── client/
│   ├── planner.py
│   ├── graph.py
│   ├── executor.py
│   ├── permissions.py
│   ├── state.py
│   └── report_generator.py
│
├── templates/
│   └── report.md.j2
│
├── configs/
│   ├── mcp-config.json
│   ├── permissions.yaml
│   └── llm.yaml
│
├── reports/
│
├── docker-compose.yml
├── requirements.txt
├── RUN.md
└── PROJECT_PLAN.md
```

---

# 6. MCP Server 设计

---

# Server 1：mining-news-mcp

## 目标

矿业新闻聚合

---

## Tool 1

### search(query, days)

输入：

```json
{
  "query": "Pilbara lithium",
  "days": 3
}
```

输出：

```json
[
  {
    "title": "",
    "url": "",
    "published_at": "",
    "summary": ""
  }
]
```

---

## Tool 2

### fetch_article(url)

输出：

```json
{
  "title": "",
  "content": ""
}
```

---

## 技术实现

- requests
- trafilatura
- RSS parsing

---

# Server 2：mineral-pdf-mcp

## 目标

PDF 矿产资源解析

---

## Tool

### extract_resources(pdf_url)

输出：

```json
{
  "measured_mt": 0,
  "indicated_mt": 0,
  "inferred_mt": 0,
  "grade_li2o": ""
}
```

---

## 提取规则

识别：

- Measured
- Indicated
- Inferred
- Mt
- Li2O %

---

## 技术实现

- pymupdf
- pdfplumber
- regex

---

# Server 3：lme-price-mcp

## 目标

矿产品行情分析

---

## Tool 1

### get_price(commodity, date)

---

## Tool 2

### get_trend(commodity, days)

输出：

```json
{
  "commodity": "Lithium",
  "current": 8200,
  "change_7d": -2.1
}
```

---

## 技术实现

初期允许 mock。

后续可接：

- AlphaVantage
- Yahoo Finance
- Benchmark Mineral

---

# 7. Agent 工作流

---

# Step 1：Intent Parsing

输入：

```text
生成 Pilbara 锂矿今日简报
```

输出：

```json
{
  "target": "Pilbara",
  "commodity": "Lithium",
  "scope": "today"
}
```

---

# Step 2：Planning

Planner 决定：

- 调哪些工具
- 顺序
- 并发执行

---

# Step 3：Permission Validation

所有工具调用必须经过权限检查。

---

# Step 4：Execution

支持并行：

```python
asyncio.gather(...)
```

---

# Step 5：Aggregation

统一状态：

```python
AgentState = {
    "news": [],
    "resources": {},
    "prices": {},
    "risks": []
}
```

---

# Step 6：Report Rendering

使用：

Jinja2

输出：

```text
reports/output.md
```

---

# 8. Agent 权限管理（重点）

必须实现权限控制。

---

# 8.1 权限模型

采用：

**RBAC + Policy Validation**

---

# 8.2 角色定义

## Planner

允许：

- 制定计划

禁止：

- 调工具

---

## Executor

允许：

- 调用 MCP Tool

禁止：

- 修改权限策略

---

## Reporter

允许：

- 生成报告

禁止：

- 发起网络请求

---

# 8.3 Tool 权限矩阵

| Tool | Allowed Role | Restriction |
|------|-------------|-------------|
| search | executor | days <= 7 |
| fetch_article | executor | allowlist domain |
| extract_resources | executor | pdf only |
| get_price | executor | approved commodity |
| get_trend | executor | days <= 30 |

---

# 8.4 URL 白名单

允许：

- mining.com
- reuters.com
- sec.gov
- sedar.com
- 官方 IR 域名

禁止：

- localhost
- 127.0.0.1
- 内网 IP
- file://

---

# 8.5 文件访问限制

允许：

```text
/reports
/tmp/downloads
```

禁止：

```text
/etc
/root
.env
config secrets
```

---

# 8.6 资源限制

## 请求超时

15 秒

---

## PDF 最大大小

50MB

---

## 最大并发

5

---

# 8.7 PermissionManager

实现：

```python
class PermissionManager:
    validate_tool_call()
    validate_url()
    validate_file_access()
    validate_resource_limits()
```

---

# 9. 安全策略

必须拒绝：

- 任意 shell 执行
- 路径穿越
- SSRF
- 非白名单 URL
- 超大文件

---

# 10. 开发 Pipeline

---

# Phase 1：项目初始化（1h）

任务：

- 初始化 repo
- requirements
- 创建目录结构

交付：

基础骨架

---

# Phase 2：MCP Server（4h）

完成：

- mining-news-mcp
- mineral-pdf-mcp
- lme-price-mcp

要求：

可独立运行

---

# Phase 3：权限系统（2h）

实现：

- permissions.py
- permissions.yaml

---

# Phase 4：Agent Core（4h）

实现：

- planner
- graph
- executor
- state

---

# Phase 5：报告生成（2h）

实现：

- Jinja2 模板
- markdown 输出

---

# Phase 6：Claude / Cursor 接入（2h）

验证：

MCP config 可直接连接

---

# Phase 7：Docker 化（2h）

实现：

- Dockerfile
- docker-compose

---

# Phase 8：测试（3h）

---

## 单元测试

每个 Tool

---

## 集成测试

完整生成日报

---

## 权限测试

非法调用必须失败

---

# 11. 验收标准

项目完成必须满足：

---

## 功能

- 成功生成日报
- 所有 MCP 可调用

---

## 权限

- 非法 URL 拒绝
- 文件越权拒绝

---

## 集成

Claude Desktop 可连接

---

## 部署

5 分钟内启动：

```bash
docker compose up
python client/main.py
```

---

# 12. Codex 执行要求

Codex 必须：

---

## 顺序执行

1. 项目骨架
2. MCP Server
3. 权限系统
4. Agent
5. 测试
6. Docker
7. RUN.md

---

## 必须遵守

- Python only
- typed code
- docstring
- modular design

---

## 禁止

- hardcode API keys
- 跳过权限验证
- unrestricted shell
- 绕过 sandbox

---

# 13. 最终交付 Checklist

## Code

- [ ] mining-news-mcp
- [ ] mineral-pdf-mcp
- [ ] lme-price-mcp
- [ ] Agent Client
- [ ] Permission Manager

---

## Config

- [ ] mcp-config.json
- [ ] permissions.yaml

---

## Infra

- [ ] docker-compose.yml

---

## Docs

- [ ] RUN.md
- [ ] Architecture.md

---

## Demo

- [ ] sample report.md
- [ ] test outputs

---

