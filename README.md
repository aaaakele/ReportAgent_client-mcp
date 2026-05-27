# Mining Daily Agent

基于 MCP（Model Context Protocol）的多工具矿业日报智能体，输入一句话即可自动生成专业矿业日报。

## 这是什么

Mining Daily Agent 是一个 AI Agent 系统，由 3 个独立 MCP Server + 1 个 Agent Client 组成。它能自动完成新闻聚合、PDF 矿产资源报告解析、矿产品行情分析，并基于 LangGraph 工作流编排，最终生成结构化的 Markdown 日报。

当你输入 `Generate Pilbara lithium daily report`，系统会自动：
1. 解析意图 → 2. 制定执行计划 → 3. 权限校验 → 4. 并行调用 MCP 工具 → 5. 聚合结果 → 6. 渲染报告

## 系统架构

```
User
  ↓
Agent Client (LangGraph)
  ↓
Planner → Permission Validator → Tool Router
  ↓                                  ↓
  ├── mining-news-mcp    (新闻聚合)
  ├── mineral-pdf-mcp    (PDF储量解析)
  └── lme-price-mcp      (行情分析)
  ↓
Aggregator → Report Generator → Markdown Report
```

## 项目结构

```
├── servers/                # MCP Servers
│   ├── mining_news/        # 新闻聚合
│   ├── mineral_pdf/        # PDF储量解析
│   └── lme_price/          # 行情分析
├── client/                 # Agent Client
│   ├── main.py             # 入口
│   ├── graph.py            # LangGraph 工作流
│   ├── planner.py          # 意图解析 & 规划
│   ├── executor.py         # 工具调用执行
│   ├── permissions.py      # 权限管理器
│   ├── state.py            # AgentState 定义
│   ├── report_generator.py # 报告生成
│   └── tests/              # 权限测试
├── templates/              # Jinja2 模板
├── configs/                # 配置文件
│   ├── mcp-config.json     # MCP 连接配置
│   ├── permissions.yaml    # 权限策略
│   └── llm.yaml            # LLM 配置
├── reports/                # 输出报告
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 LLM

```bash
# 至少配置一个 LLM provider
export OPENAI_API_KEY="sk-..."

# 或者使用 DeepSeek (修改 configs/llm.yaml: default_provider: deepseek)
export DEEPSEEK_API_KEY="sk-..."

# 或者使用 Anthropic (修改 configs/llm.yaml: default_provider: anthropic)
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. 运行 Agent

```bash
PYTHONPATH=. python -m client.main "Generate Pilbara lithium daily report"
```

### 4. 查看报告

报告会生成在 `reports/` 目录下。

## Docker 一键启动

```bash
docker compose up -d
docker compose logs -f agent
```

## 运行测试

```bash
# 全部测试
pytest -v

# 特定模块
pytest servers/mining_news/tests/ -v
pytest servers/mineral_pdf/tests/ -v
pytest servers/lme_price/tests/ -v
pytest client/tests/ -v
```

## MCP Server 独立运行

```bash
# mining-news-mcp (新闻聚合)
PYTHONPATH=. python -m servers.mining_news.server

# mineral-pdf-mcp (PDF储量解析)
PYTHONPATH=. python -m servers.mineral_pdf.server

# lme-price-mcp (行情分析)
PYTHONPATH=. python -m servers.lme_price.server
```

## Claude Desktop / Cursor 集成

将 `configs/mcp-config.json` 添加到 Claude Desktop 的 MCP 配置中：

```json
{
  "mcpServers": {
    "mining-news": {
      "command": "python",
      "args": ["-m", "servers.mining_news.server"],
      "env": {}
    },
    "mineral-pdf": {
      "command": "python",
      "args": ["-m", "servers.mineral_pdf.server"],
      "env": {}
    },
    "lme-price": {
      "command": "python",
      "args": ["-m", "servers.lme_price.server"],
      "env": {}
    }
  }
}
```

## 权限模型

项目实现了完整的 RBAC + Policy Validation 权限控制：

| Tool | Allowed Role | Restriction |
|------|-------------|-------------|
| search_news | executor | days <= 7 |
| fetch_article | executor | URL 白名单域名 |
| extract_resources | executor | 仅 PDF, 最大 50MB |
| get_price | executor | 仅已批准的矿产品 |
| get_trend | executor | days <= 30, 已批准的矿产品 |

- **URL 白名单**: mining.com, reuters.com, sec.gov, sedar.com 等官方矿业/金融域名
- **URL 黑名单**: localhost, 127.0.0.1, 内网 IP, file:// 协议
- **文件访问**: 仅允许 `/reports` 和 `/tmp/downloads` 路径
- **资源限制**: 请求超时 15 秒, PDF 上限 50MB, 最大并发 5

## 技术栈

| 层级 | 技术 |
|------|------|
| MCP 框架 | FastMCP |
| Agent 编排 | LangGraph + LangChain |
| LLM | OpenAI / DeepSeek / Anthropic |
| PDF 解析 | pdfplumber + PyMuPDF |
| 新闻抓取 | trafilatura + feedparser |
| 报告渲染 | Jinja2 |
| 容器化 | Docker + docker-compose |
| 测试 | pytest + pytest-asyncio |

## 示例报告

```
# Pilbara Lithium Daily Report (Sample)

Date: 2026-05-26 08:00

## Today's Highlights
- Retrieved 3 news articles related to Pilbara Lithium.
- Lithium Carbonate (Li2CO3): 82000 CNY/tonne (Trend: downward)
- Spodumene Concentrate (6% Li2O): 890 USD/tonne (Trend: downward)

## News Summary
...

## Resource Estimates
| Category  | Value     |
|-----------|-----------|
| Measured  | 198.0 Mt  |
| Indicated | 164.0 Mt  |
| Inferred  | 68.0 Mt   |
| Total     | 430.0 Mt  |
| Grade     | 1.15% Li2O |

## Market Price Analysis
...
```

完整示例见 [reports/sample_report.md](reports/sample_report.md)。

## 关于作者

这个项目的初衷很简单：矿业分析领域的信息实在太分散了——新闻散落在各个网站、储量数据藏在 PDF 报告里、价格行情需要在不同平台间切换。一个分析师每天光是收集信息就要花掉大半天。所以我构建了 Mining Daily Agent，用 MCP 协议将不同数据源标准化，再用 LangGraph 编排 Agent 工作流，让一句话就能生成一份完整的矿业日报。

项目的核心思路是 **关注点分离**：三个 MCP Server 各司其职（新闻、储量、行情），Agent Client 负责任务编排和报告生成，权限层保证安全性。这种设计让每个模块都可以独立开发、独立测试、独立部署。

欢迎提 Issue 和 PR，一起把矿业分析变得更智能。


