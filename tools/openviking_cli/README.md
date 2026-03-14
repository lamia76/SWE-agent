# OpenViking Tool Bundle for SWE-agent（嵌入式模式）

与 **tools/openviking** 相同逻辑：使用 SyncOpenViking SDK **本地嵌入式调用**，无需远程 Server。配置 **ov.conf** 中的 embedding/vlm/rerank API 地址即可。

## 配置（仅本目录）

| 文件 | 说明 |
|------|------|
| **ov.conf** | 与 tools/openviking 格式相同：embedding、vlm、rerank、storage、parsers 等。 |

## 功能与工具列表

与 tools/openviking 相同的 8 个工具（签名一致）：

1. **ov_index_repo** - 索引仓库
2. **ov_wait** - 等待处理完成
3. **ov_find** - 语义搜索
4. **ov_abstract** - 极简摘要 L0
5. **ov_overview** - 结构化概览 L1
6. **ov_read** - 完整内容 L2
7. **ov_ls** - 列出目录
8. **ov_glob** - 按模式查找

## 安装

```bash
cd SWE-agent/tools/openviking_cli
./install.sh
```

安装脚本会：安装 OpenViking SDK、设置 `OPENVIKING_CONFIG_FILE` 指向 ov.conf、`OPENVIKING_DATA_DIR`、PATH。若存在 `tls-ca-bundle.pem` 则设置证书环境变量。

## 配置（仅改本目录 ov.conf）

编辑 **tools/openviking_cli/ov.conf**，配置：

- **embedding.dense**：`api_base`、`api_key`、`model` 等（向量化服务）
- **vlm**：`api_base`、`api_key`、`model` 等（摘要生成）
- **rerank**：可选，用于搜索重排序

与 tools/openviking 使用同一套模型接口（如 8002、10193 等）。

## 快速开始

```bash
./install.sh
ov_index_repo .
ov_wait
ov_find "authentication error" -k 5
ov_abstract viking://path/to/file.py
ov_read viking://path/to/file.py --max-chars 16000
```

## 在 SWE-agent 中使用

```yaml
tool_bundles:
  - openviking_cli
```

确保已执行 `./install.sh`，并按需编辑 **ov.conf** 中的 embedding/vlm/rerank API。

## 证书（HTTPS/自签名 CA）

将 **tls-ca-bundle.pem** 放在本目录下，embedding/vlm 使用 HTTPS 自签名时 install 会自动设置证书。详见 `RUN_WITH_SSL_CERT.md`。

## 故障排除

- **OpenViking SDK 未安装**：执行 `./install.sh`。
- **初始化失败**：检查 **ov.conf** 的 embedding/vlm api_base 与网络；HTTPS 自签名时配置 tls-ca-bundle.pem。

## 许可证

与 SWE-agent、tools/openviking 一致；OpenViking 见 https://github.com/volcengine/OpenViking 。
