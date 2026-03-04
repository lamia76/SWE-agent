# OpenViking Proxy Bundle for SWE-agent

以 SWE-agent Tool 形式通过 **HTTP 代理** 接入 OpenViking，使运行在容器内的 agent 可调用 OpenViking 的读取、搜索、列表等能力。

**接口与参数以 OpenViking 目录为准**（`OpenViking/openviking_cli/client/base.py`、`OpenViking/openviking/server/routers/*` 及官方文档），与 **swe-agent/tools/openviking** 下的 ov_* 封装无关；本 bundle 的工具名与参数名、语义与 OpenViking 项目 API 一致。

## 功能特性

- **语义搜索**：`openviking_search` 对应 OpenViking `find`（query、target_uri、limit、score_threshold）
- **分层读取**：`openviking_read` 对应 content API：abstract(uri)、overview(uri)、read(uri)，level=abstract|overview|read
- **目录与模式**：`openviking_list` 对应 fs/ls（uri、simple、recursive、node_limit）；`openviking_grep` / `openviking_glob` 对应 search/grep、search/glob
- **用户记忆**：`user_memory_search` 在 viking://user/.../memories/ 中搜索

与 [tools/openviking](../openviking/README.md) 的差异：tools/openviking 为 SWE-agent 自有的 ov_* 封装；本 bundle 在**主机**运行 Proxy，容器内通过 HTTP 调用，**参数对齐 OpenViking 项目**，便于与 OpenViking 版本同步。

## 安装

### 自动安装（主机侧）

在**主机**上执行本 bundle 提供的安装脚本（与 tools/openviking 的 `./install.sh` 用法一致）：

```bash
cd tools/openviking_proxy
./install.sh
```

安装脚本会：
- 检查 Python 与 pip 环境
- 安装 OpenViking SDK
- 将 `OPENVIKING_CONFIG_FILE` 指向本目录下的 `ov.conf.third_party_api`
- 创建 `~/.vikingbot` 目录（VikingClient 需在此或通过环境变量提供配置）

### 手动安装（主机侧）

```bash
pip install openviking
```

Proxy 依赖 **VikingClient**（来自 OpenViking/bot），任选其一：

- 将 OpenViking/bot 加入 PYTHONPATH：`export PYTHONPATH="/path/to/OpenViking/bot:$PYTHONPATH"`
- 或在 OpenViking/bot 目录执行：`pip install -e .`

## 配置

### 环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| `OPENVIKING_CONFIG_FILE` | OpenViking 配置文件路径（主机） | 安装脚本会设为 `tools/openviking_proxy/ov.conf.third_party_api` |
| `OPENVIKING_PROXY_URL` | 容器内访问 Proxy 的 URL | `http://host.docker.internal:8765` |
| `OPENVIKING_DATA_DIR` | 数据目录（若 OpenViking 使用本地存储） | 由 ov.conf 指定 |

### 配置文件

配置文件放在本 tools 目录下，便于版本管理与复用（与 tools/openviking 的 `ov.conf` 用法一致）：

```bash
# 使用本目录提供的第三方 API 示例配置
export OPENVIKING_CONFIG_FILE=/path/to/SWE-agent/tools/openviking_proxy/ov.conf.third_party_api

# 或复制到默认路径
mkdir -p ~/.openviking
cp tools/openviking_proxy/ov.conf.third_party_api ~/.openviking/ov.conf
```

Proxy 使用的 **VikingClient** 会读取 `~/.vikingbot/config.json`，请按需配置 local 或 remote 模式。

### 索引目标仓库（必须）

在使用 `openviking_read` / `openviking_search` 前，需在**主机**上先把目标仓库或目录添加进 OpenViking（与 tools/openviking 的 `ov_index_repo` 等价）：

```bash
# 确保 OpenViking 服务已就绪（local 模式随 VikingClient 自动拉起；remote 则先起 openviking-server）

# 添加远程仓库
openviking add-resource https://github.com/owner/repo --wait --timeout 300

# 添加本地目录
openviking add-resource /path/to/target/repo --to viking://resources/ --wait

# 查看已索引资源
openviking ls viking://resources/
```

未执行 `add-resource` 时，`viking://resources/` 下无数据，read/search 将无结果。

## 使用步骤

### 1. 在主机上启动 Proxy Server

```bash
# 若未用 pip 安装 vikingbot，需将 OpenViking/bot 加入 PYTHONPATH
export PYTHONPATH="/path/to/OpenViking/bot:$PYTHONPATH"

# 可选：指定本 bundle 的配置
export OPENVIKING_CONFIG_FILE=/path/to/SWE-agent/tools/openviking_proxy/ov.conf.third_party_api

# 启动代理（默认端口 8765）
cd tools/openviking_proxy
python proxy_server.py

# 或指定端口与 host
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
      - path: tools/openviking_proxy
    propagate_env_variables:
      - OPENVIKING_PROXY_URL
```

### 3. 容器访问主机的网络配置

- **Docker Desktop (Win/Mac)**：默认可用 `host.docker.internal`
  ```bash
  export OPENVIKING_PROXY_URL=http://host.docker.internal:8765
  ```
- **Linux Docker**：需把主机 IP 暴露给容器
  ```bash
  docker run --add-host=host.docker.internal:host-gateway ...
  # 或
  export OPENVIKING_PROXY_URL=http://172.17.0.1:8765
  ```

未设置 `OPENVIKING_PROXY_URL` 时，默认使用 `http://host.docker.internal:8765`。

### 4. 运行 SWE-agent

```bash
sweagent run \
  --config config/your_config.yaml \
  --agent.tools.bundles.3.path=tools/openviking_proxy
```

## 可用工具（对齐 OpenViking 目录 API）

本 bundle 暴露的工具及参数与 **OpenViking 项目** 一致（非 tools/openviking 的 ov_*）：

| 工具名 | 对应 OpenViking API / tools/openviking | 主要参数 |
|--------|----------------------------------------|----------|
| `openviking_add_resource` | resources 添加 / **ov_index_repo** | path（URL 或主机路径）, reason, target, wait |
| `openviking_read` | content/abstract、overview、read | uri, level（abstract\|overview\|read） |
| `openviking_list` | fs/ls | uri, simple, recursive, node_limit |
| `openviking_search` | search/find | query, target_uri, limit, score_threshold |
| `openviking_grep` | search/grep | uri, pattern, case_insensitive, node_limit |
| `openviking_glob` | search/glob | pattern, uri |
| `user_memory_search` | find(target_uri=user/memories) | query |

### 工具详解（与 OpenViking 文档一致）

- **openviking_add_resource**：对应 OpenViking `add_resource` / tools/openviking 的 **ov_index_repo**。将 path（URL 或主机可访问路径）加入 OpenViking 并建索引，之后方可 search/read。可选 reason、target（如 viking://resources/）、wait。
- **openviking_read**：对应 `abstract(uri)` L0、`overview(uri)` L1、`read(uri)` L2。
- **openviking_list**：对应 `ls(uri, simple, recursive, node_limit)`，默认 uri 为 `viking://resources/`。
- **openviking_search**：对应 `find(query, target_uri, limit, score_threshold)`，limit 默认 10。
- **openviking_grep**：对应 `grep(uri, pattern, case_insensitive, node_limit)`。
- **openviking_glob**：对应 `glob(pattern, uri)`，uri 默认 `viking://`。
- **user_memory_search**：在 `viking://user/.../memories/` 下语义搜索。

## 架构设计

与 tools/openviking 一致，本 bundle 将「安装、配置、API 暴露」均收敛在 tools 目录内；差异在于 openviking 为进程内 SDK 调用，openviking_proxy 为跨进程 HTTP 代理：

```
┌─────────────────────────────────┐     HTTP POST      ┌──────────────────────────┐
│  SWE-agent 容器                  │  ──────────────►  │  主机 Proxy Server       │
│  bin/openviking_read 等脚本      │                   │  proxy_server.py         │
│  (env.communicate 执行)          │  ◄──────────────  │  调用 VikingClient       │
└─────────────────────────────────┘      JSON 结果     └──────────────────────────┘
```

- 容器内：`bin/*` 脚本通过 `lib/ov_proxy_client.py` 请求主机 Proxy。
- 主机：`proxy_server.py` 使用 VikingClient 调用 OpenViking，读取 `~/.vikingbot/config.json` 与 `OPENVIKING_CONFIG_FILE`。

## 故障排除

- **Cannot import VikingClient**：确保 OpenViking/bot 在 PYTHONPATH 或已 `pip install -e .`（在 bot 目录）。
- **搜索结果为空**：先在主机执行 `openviking add-resource <path-or-url> --wait` 完成索引，再使用 read/search。
- **容器连不上 Proxy**：检查 `OPENVIKING_PROXY_URL` 与 Docker 网络（如 `host.docker.internal`、`host-gateway`）。

## 第三方 API 与 TLS 证书

使用自签名或私有 CA 证书时，详见 [RUN_WITH_SSL_CERT.md](RUN_WITH_SSL_CERT.md)。

- `ov.conf.third_party_api`：本目录下的第三方 API 示例配置（embedding、vlm、rerank 等）
- `tls-ca-bundle.pem`：放入本目录后，`run_with_ssl.sh` 会自动加载
- 快速启动（带 SSL）：`./run_with_ssl.sh`

## 参考

- **接口与参数以 OpenViking 项目为准**：`OpenViking/openviking_cli/client/base.py`、`OpenViking/openviking/server/routers/`、`OpenViking/docs/`。
- SWE-agent 自有 ov_* 封装（非本 bundle 对齐对象）：[tools/openviking/README.md](../openviking/README.md)
- OpenViking 项目：https://github.com/volcengine/OpenViking
