# OpenViking CLI Tool Bundle for SWE-agent

基于**最新 OpenViking 仓库**，使用 **CLI 方式通过 HTTP** 调用 OpenViking：Agent 通过 `ov` / `openviking` 命令连接已部署的 **OpenViking Server**。模型为**本地部署**，请求的 **URL 与 API Key** 与 **tools/openviking 下的 ov.conf** 配置一致。

## 使用方式与配置对应关系

| 角色 | 配置文件 | 说明 |
|------|----------|------|
| **SWE Agent（调用方）** | **ovcli.conf** | 仅配置 OpenViking Server 的 `url`、`api_key`（与 tools/openviking 部署同机时默认 `http://141.61.16.3:1933`） |
| **OpenViking Server** | **ov.conf** | 与 tools/openviking 的 ov.conf 一致：embedding / vlm / rerank 的 api_base、api_key、host 等，用于本地部署模型 |

本 bundle 内同时提供：

- **ovcli.conf**：给 CLI 客户端用，指定连哪台 Server（url/api_key）。
- **ov.conf**：与 tools/openviking 的 ov.conf 一致，供 **启动 OpenViking Server 时**使用，保证模型请求的 URL 和 API Key 与 tools/openviking 一致。

## 功能与工具列表

与 tools/openviking 相同的 8 个工具（签名一致）：

1. **ov_index_repo** - 索引仓库（`ov add-resource`）
2. **ov_wait** - 等待处理完成（`ov system wait`）
3. **ov_find** - 语义搜索（`ov find`）
4. **ov_abstract** - 极简摘要 L0（`ov abstract`）
5. **ov_overview** - 结构化概览 L1（`ov overview`）
6. **ov_read** - 完整内容 L2（`ov read`）
7. **ov_ls** - 列出目录（`ov ls`）
8. **ov_glob** - 按模式查找（`ov glob`）

## 安装（SWE 侧）

```bash
cd SWE-agent/tools/openviking_cli
./install.sh
```

安装脚本会：安装 OpenViking SDK、设置 `OPENVIKING_CLI_CONFIG_FILE` 指向本目录的 ovcli.conf、**若本目录下有 tls-ca-bundle.pem 则自动设置证书环境变量**（RUN_WITH_SSL_CERT 逻辑已合并，证书放同目录即可）、PATH。

## 启动 OpenViking Server（模型侧）

在**部署 embedding/vlm 的机器上**（或能访问这些模型 URL 的机器上）启动 Server，并使用与 tools/openviking **相同的 ov.conf**（本 bundle 已提供一份）：

```bash
cd SWE-agent/tools/openviking_cli
chmod +x start_server.sh
./start_server.sh
# 或指定配置： ./start_server.sh /path/to/ov.conf
```

或直接使用环境变量 + 命令：

```bash
export OPENVIKING_CONFIG_FILE=/path/to/SWE-agent/tools/openviking_cli/ov.conf
openviking-server --config "$OPENVIKING_CONFIG_FILE"
```

本 bundle 中的 **ov.conf** 与 **tools/openviking/ov.conf** 在 embedding、vlm、rerank 的 url/api_key 上保持一致（本地部署的模型地址与接口）。

## 配置说明

### ovcli.conf（客户端，本 bundle 已配好）

- **url**：OpenViking Server 地址，默认 `http://141.61.16.3:1933`（与 tools/openviking 部署一致）。
- **api_key**：若 Server 配置了 `server.root_api_key`，此处填写；否则保持 `null`。

### ov.conf（服务端，本 bundle 已提供）

- **server**：Server 监听地址，默认 `0.0.0.0:1933`；可按需改 `host`/`port`、`root_api_key`。
- **embedding / vlm / rerank**：与 tools/openviking/ov.conf 一致，使用本地部署的模型 URL 和 API Key（如 `api_base`、`api_key`、`host`）。

### 证书（HTTPS/自签名 CA）

将 **tls-ca-bundle.pem** 放在本目录下（与 install.sh 同目录），执行 install.sh 后会自动设置 `REQUESTS_CA_BUNDLE`、`SSL_CERT_FILE`；各 bin 脚本运行时也会检测该文件。详见 `RUN_WITH_SSL_CERT.md`。

## 在 SWE-agent 中使用

在任务的 tool_bundles 中引用本 bundle：

```yaml
tool_bundles:
  - openviking_cli
```

确保已执行 `tools/openviking_cli/install.sh`，且 PATH 中包含本 bundle 的 bin 或 Python 的 bin。

## 快速开始

```bash
# 1. 在模型所在机启动 Server（使用本 bundle 的 ov.conf）
./start_server.sh

# 2. 在 SWE 环境安装并调用
./install.sh
ov_index_repo .
ov_wait
ov_find "authentication error" -k 5
ov_abstract viking://path/to/file.py
ov_read viking://path/to/file.py --max-chars 16000
```

## 故障排除

- **未找到 ov / openviking**：执行 `./install.sh`，确认 `pip install openviking` 且 PATH 含 Python bin。
- **连接 Server 失败**：检查 ovcli.conf 的 `url`、Server 是否已启动、网络与防火墙；HTTPS 时见 `RUN_WITH_SSL_CERT.md`。
- **鉴权失败**：若 Server 配置了 `root_api_key`，在 ovcli.conf 中填写对应 `api_key`。

## 许可证

与 SWE-agent、tools/openviking 一致；OpenViking 见 https://github.com/volcengine/OpenViking 。
