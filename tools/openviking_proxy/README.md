# OpenViking Proxy Bundle

以 SWE-agent Tool 形式导入 OpenViking，使 SWE-agent 在容器内可调用 OpenViking 的读取、搜索、列表等能力。

## 架构

```
┌─────────────────────────────────┐     HTTP POST      ┌──────────────────────────┐
│  SWE-agent 容器                  │  ──────────────►  │  主机 Proxy Server       │
│  bin/openviking_read 等脚本      │                   │  proxy_server.py         │
│  (env.communicate 执行)          │  ◄──────────────  │  调用 VikingClient       │
└─────────────────────────────────┘      JSON 结果     └──────────────────────────┘
```

## 使用步骤

### 1. 在主机上启动 Proxy Server

Proxy 需在主机运行，以便访问 OpenViking 数据和配置。

```bash
# 将 OpenViking/bot 加入 PYTHONPATH
export PYTHONPATH="/path/to/OpenViking/bot:$PYTHONPATH"

# 启动代理（默认端口 8765）
cd SWE-agent/tools/openviking_proxy
python proxy_server.py

# 或指定端口和 host
python proxy_server.py --port 8765 --host 0.0.0.0
```

### 2. 配置 SWE-agent

在 agent 配置的 `tools.bundles` 中加入 openviking_proxy：

```yaml
agent:
  templates:
    instance_template: |-
      ...
      You can use OpenViking tools (openviking_read, openviking_search, user_memory_search, etc.)
      to read and search context from the OpenViking knowledge base.
    tools:
      bundles:
        - path: tools/registry
        - path: tools/edit_anthropic
        - path: tools/review_on_submit_m
        - path: tools/openviking_proxy   # 新增
      propagate_env_variables:
        - OPENVIKING_PROXY_URL   # 可选，用于指定代理 URL
```

### 3. 容器访问主机的网络配置

- **Docker Desktop (Win/Mac)**：默认可用 `host.docker.internal`
  ```bash
  export OPENVIKING_PROXY_URL=http://host.docker.internal:8765
  ```

- **Linux Docker**：需要把主机 IP 暴露给容器
  ```bash
  docker run --add-host=host.docker.internal:host-gateway ...
  # 或
  export OPENVIKING_PROXY_URL=http://172.17.0.1:8765
  ```

若未设置 `OPENVIKING_PROXY_URL`，默认使用 `http://host.docker.internal:8765`。

### 4. 运行 SWE-agent

```bash
sweagent run \
  --config config/your_config.yaml \
  --agent.tools.bundles.3.path=tools/openviking_proxy
```

## 可用工具

| 工具名 | 说明 |
|--------|------|
| `openviking_read` | 读取 OpenViking 资源（abstract/overview/read 三种粒度） |
| `openviking_list` | 列出指定路径下的资源 |
| `openviking_search` | 按查询搜索资源 |
| `openviking_grep` | 使用正则 grep 搜索 |
| `openviking_glob` | 按 glob 模式查找文件 |
| `user_memory_search` | 搜索用户记忆 |

## OpenViking 配置

Proxy Server 使用 VikingClient，会读取 `~/.vikingbot/config.json`。请确保 OpenViking 已正确配置（local 或 remote 模式）。
