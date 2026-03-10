# OpenViking (local CLI) Bundle for SWE-agent

本 bundle 与 **tools/openviking** 使用**相同的调用方式**：在容器内安装 OpenViking CLI（`ov_*` 命令），通过 **ov.conf** 使用 OpenViking 服务（本地向量库 + 远程 embedding/vlm/rerank 等）。无需单独起 Proxy 或配置 `OPENVIKING_PROXY_URL`。

## 工具列表（与 tools/openviking 一致）

| 工具 | 说明 |
|------|------|
| `ov_index_repo` | 索引目标仓库，首次或大变更后必须执行 |
| `ov_wait` | 等待索引进度完成 |
| `ov_find` | 语义搜索 |
| `ov_abstract` | 极简摘要（L0） |
| `ov_overview` | 结构化概览（L1） |
| `ov_read` | 完整内容（L2） |
| `ov_ls` | 列出目录 |
| `ov_glob` | 按模式查找文件 |

## 安装与配置

安装脚本在**容器内**执行（SWE-agent 启动环境时自动执行）：

- 安装 OpenViking SDK：`pip install openviking`
- 设置 `OPENVIKING_CONFIG_FILE` 指向本目录的 `ov.conf`（若存在）或 `ov.conf.third_party_api`
- 设置 `OPENVIKING_DATA_DIR`（默认 `./.openviking`）

`ov_*` 命令由 openviking 包提供，通过 PATH 调用；本 bundle 的 `bin/` 仅保留占位，不提供可执行脚本。

## 配置文件

- **ov.conf**：与 tools/openviking 同格式，供 OpenViking CLI 使用（embedding、vlm、rerank 等可指向你的 API）。
- **ov.conf.third_party_api**：备用配置，若存在 `ov.conf` 则优先使用 `ov.conf`。

按需修改 `api_base`、`api_key` 等以指向你的 embedding/vlm 服务。

## 使用步骤

1. 在配置中启用本 bundle（与 openviking 二选一或替换）：

   ```yaml
   tools:
     bundles:
       - path: tools/openviking_proxy
   ```

2. 在任务环境中先索引再搜索，例如：

   ```bash
   cd /testbed
   ov_index_repo .
   ov_wait
   ov_find "your query"
   ov_abstract viking://path/to/file.py
   ov_read viking://path/to/file.py --max-chars 16000
   ```

## 与 tools/openviking 的差异

- **调用方式相同**：都使用本地 `ov_*` 命令 + `ov.conf`，不依赖 HTTP Proxy。
- **配置与命名**：本 bundle 保留 `openviking_proxy` 目录名，可继续使用本目录下的 `ov.conf` / `ov.conf.third_party_api`；若需与 openviking 完全一致，可改用 `tools/openviking` 并共用其配置。

## 可选：Proxy 与 VikingClient

本目录仍保留 `proxy_server.py` 与 `lib/ov_proxy_client.py`，供在**主机**上单独起 Proxy、由其他客户端通过 HTTP 调用的场景使用。使用本 bundle 的「本地 ov_*」方式时，**不需要**启动 Proxy 或配置 `OPENVIKING_PROXY_URL`。

## 参考

- 同仓库 [tools/openviking/README.md](../openviking/README.md)
- OpenViking：https://github.com/volcengine/OpenViking
