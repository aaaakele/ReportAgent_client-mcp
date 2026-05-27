# RUN.md — Mining Daily Agent 运行指南

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置环境变量

```bash
# 至少配置一个 LLM provider
export OPENAI_API_KEY="sk-..."

# 或者使用 DeepSeek
export DEEPSEEK_API_KEY="sk-bd83af914c054210bd75ac2dce674b46"
# 修改 configs/llm.yaml: default_provider: deepseek

# 或者使用 Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
# 修改 configs/llm.yaml: default_provider: anthropic
```

### 3. 运行 Agent

```bash
# 从项目根目录运行
PYTHONPATH=. python -m client.main "Generate Pilbara lithium daily report"
```

### 4. 查看报告

```bash
ls reports/
# report_20260126_120000.md
```

---

## Docker 一键启动

```bash
docker compose up -d
docker compose logs -f agent
```

报告会生成在 `./reports/` 目录。

---

## 运行测试

```bash
# 运行全部测试
pytest -v

# 运行特定模块测试
pytest servers/mining_news/tests/ -v
pytest servers/mineral_pdf/tests/ -v
pytest servers/lme_price/tests/ -v
pytest client/tests/ -v
```

---

## MCP Server 独立运行

### mining-news-mcp

```bash
PYTHONPATH=. python -m servers.mining_news.server
```

### mineral-pdf-mcp

```bash
PYTHONPATH=. python -m servers.mineral_pdf.server
```

### lme-price-mcp

```bash
PYTHONPATH=. python -m servers.lme_price.server
```

---

## Claude Desktop / Cursor 集成

将 `configs/mcp-config.json` 中的配置添加到 Claude Desktop 的 MCP 配置中：
claude 输出结果（https://claude.ai/share/0144efd7-a227-4c1f-a920-3dd8a7cf829f）
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

---

## 项目结构

```
mining-daily-agent/
├── servers/               # MCP Servers
│   ├── mining_news/       # 新闻聚合
│   ├── mineral_pdf/       # PDF储量解析
│   └── lme_price/         # 行情分析
├── client/                # Agent Client
│   ├── main.py            # 入口
│   ├── graph.py           # LangGraph 工作流
│   ├── planner.py         # 意图解析 & 规划
│   ├── executor.py        # 工具调用执行
│   ├── permissions.py     # 权限管理器
│   ├── state.py           # AgentState 定义
│   ├── report_generator.py # 报告生成
│   └── tests/             # 权限测试
├── templates/             # Jinja2 模板
├── configs/               # 配置文件
│   ├── mcp-config.json    # MCP 连接配置
│   ├── permissions.yaml   # 权限策略
│   └── llm.yaml           # LLM 配置
├── reports/               # 输出报告
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── CLAUDE.md
```

---

## 权限模型

项目实现了完整的 RBAC + Policy Validation：

| Tool | Allowed Role | Restriction |
|------|-------------|-------------|
| search_news | executor | days <= 7 |
| fetch_article | executor | whitelist domain only |
| extract_resources | executor | PDF only, max 50MB |
| get_price | executor | approved commodity only |
| get_trend | executor | days <= 30, approved commodity |

### URL 白名单

允许访问: mining.com, reuters.com, sec.gov, sedar.com 等

禁止访问: localhost, 127.0.0.1, 内网 IP, file://

### 文件访问限制

允许: `/reports`, `/tmp/downloads`

禁止: `/etc`, `/root`, `.env`, config secrets
