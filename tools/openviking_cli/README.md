# OpenViking CLI Tool Bundle for SWE-agent

通过 **ov 命令** 连接已部署的 OpenViking Server（HTTP）。模型在他处部署，**配置 ovcli.conf 的 url 即可调用**。

## 配置（仅本目录）

| 文件 | 说明 |
|------|------|
| **ovcli.conf** | `url`（OpenViking Server 地址，如 http://host:8090）、`api_key`（可选） |

## 功能与工具列表

与 tools/openviking 相同的 8 个工具（通过 ov 命令调用 Server）：

1. **ov_index_repo** - ov add-resource
2. **ov_wait** - ov system wait
3. **ov_find** - ov find
4. **ov_abstract** - ov abstract (L0)
5. **ov_overview** - ov overview (L1)
6. **ov_read** - ov read (L2)
7. **ov_ls** - ov ls
8. **ov_glob** - ov glob

## 安装

```bash
cd SWE-agent/tools/openviking_cli
./install.sh
```

安装会：安装 OpenViking SDK、设置 `OPENVIKING_CLI_CONFIG_FILE` 指向 ovcli.conf、PATH、可选 TLS 证书。

## 配置

编辑 **ovcli.conf**：
- **url**：OpenViking Server 的 HTTP 地址（如 `http://141.61.16.3:8090`）
- **api_key**：若 Server 启用了鉴权则填写

或设置环境变量 `OPENVIKING_SERVER_URL`（优先于 ovcli.conf）。

## 快速开始

```bash
./install.sh
ov_index_repo .
# 默认只上传资源不等待；若需立即搜索，加 --wait 或之后运行 ov_wait
ov_index_repo . --wait   # 或先 ov_wait 再 ov_find
ov_find "authentication error" -k 5
ov_abstract viking://path/to/file.py
ov_read viking://path/to/file.py --max-chars 16000
```

## 在 SWE-agent 中使用

```yaml
tool_bundles:
  - openviking_cli
```

确保已执行 `./install.sh`，并配置 **ovcli.conf** 的 url。

## 证书（HTTPS/自签名 CA）

将 **tls-ca-bundle.pem** 放在本目录，install 会自动设置证书环境变量。详见 `RUN_WITH_SSL_CERT.md`。

## 故障排除

- **连接失败**：检查 ovcli.conf 的 url 与网络；HTTPS 自签名时配置 tls-ca-bundle.pem。
- **`ov_find` 立刻返回 total 0**：多为索引后后台队列（向量化等）尚未完成。`ov_index_repo` 默认不等待；请在搜索前执行 **`ov_wait`**，或使用 `ov_index_repo . --wait`。
