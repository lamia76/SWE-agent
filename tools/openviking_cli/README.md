# OpenViking CLI Tool Bundle for SWE-agent

基于 OpenViking，使用 **CLI 方式通过 HTTP** 调用已部署的 OpenViking 服务。模型已在他处部署，**仅需配置 ovcli.conf 的 url 即可直接调用**，无需本地启动 Server。

## 配置（仅本目录）

| 文件 | 说明 |
|------|------|
| **ovcli.conf** | API 连接配置：`url`（已部署的 OpenViking 服务地址）、`api_key`（可选）。 |

install 与各 bin 脚本仅读取本目录的 ovcli.conf，设置 `OPENVIKING_CLI_CONFIG_FILE` 后调用 ov 命令，不引用其他目录。

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

安装脚本会：安装 OpenViking SDK、设置 `OPENVIKING_CLI_CONFIG_FILE` 指向本目录 ovcli.conf、若本目录下有 tls-ca-bundle.pem 则设置证书环境变量、PATH。

## 配置 API 接口（仅改本目录 ovcli.conf）

编辑 **tools/openviking_cli/ovcli.conf**：

- **url**：已部署 OpenViking 服务的 HTTP 地址（如 `http://141.61.16.3:8090`）
- **api_key**：若服务启用了鉴权则填写，否则保持 `null`

## 单独测试 openviking_cli 调用方式

不依赖 SWE-agent 运行整个 benchmark，也可以在本地快速验证 CLI 是否可用。

### 前提

- 已有可访问的 OpenViking 服务（模型已在他处部署），地址记为 `http://YOUR_OV_SERVER:8090`
- 本机可访问该地址（如有代理，设置 `no_proxy` 等）

### 步骤一：配置 ovcli.conf

在本目录编辑 `ovcli.conf`，确认至少包含：

```toml
url = "http://YOUR_OV_SERVER:8090"
api_key = null  # 如需鉴权则改为实际 key
```

### 步骤二：安装并加载环境

在项目根目录或本目录终端执行：

```bash
cd SWE-agent/tools/openviking_cli
./install.sh
```

该脚本会：

- 安装/升级 OpenViking Python 包
- 设置 `OPENVIKING_CLI_CONFIG_FILE` 指向本目录的 `ovcli.conf`
- 将 Python 的 bin 目录加入 `PATH`
- 若存在 `tls-ca-bundle.pem`，自动设置证书相关环境变量

### 步骤三：用 ov 原生命令测试

安装完成后，直接调用 ov 命令测试链路：

```bash
# 列出 viking 根目录，验证连通性
ov ls viking://

# 语义搜索测试
ov find "hello world" -n 3
```

如能返回结果，说明 CLI 调用链路正常。

### 步骤四：用 bundle 封装命令测试

也可以测试本目录提供的封装脚本是否工作正常：

```bash
cd SWE-agent/tools/openviking_cli

# 索引当前仓库
./bin/ov_index_repo .

# 等待索引完成
./bin/ov_wait

# 搜索
./bin/ov_find "hello world" -k 5

# 查看摘要 / 读取内容（用实际 viking:// 路径替换）
./bin/ov_abstract viking://path/to/file.py
./bin/ov_read viking://path/to/file.py --max-chars 16000
```

如果上述命令均返回正常结果，则可以认为 openviking_cli 工具 bundle 在当前环境下是可用的。

## 证书（HTTPS/自签名 CA）

将 **tls-ca-bundle.pem** 放在本目录下，install 与各 bin 脚本会自动设置 `REQUESTS_CA_BUNDLE`、`SSL_CERT_FILE`。详见 `RUN_WITH_SSL_CERT.md`。

## 在 SWE-agent 中使用

```yaml
tool_bundles:
  - openviking_cli
```

确保已执行 `tools/openviking_cli/install.sh`，并按需编辑本目录 **ovcli.conf** 的 url/api_key。

## 快速开始

```bash
# 1. 编辑本目录 ovcli.conf，设置 url（及可选 api_key）
# 2. 安装并调用
./install.sh
ov_index_repo .
ov_wait
ov_find "authentication error" -k 5
ov_abstract viking://path/to/file.py
ov_read viking://path/to/file.py --max-chars 16000
```

## 故障排除

- **未找到 ov / openviking**：执行 `./install.sh`，确认 PATH 含 Python bin。
- **连接失败**：检查 **ovcli.conf** 的 `url` 与网络；HTTPS 时见 `RUN_WITH_SSL_CERT.md`。
- **鉴权失败**：在 **ovcli.conf** 中设置正确的 `api_key`。

## 许可证

与 SWE-agent、tools/openviking 一致；OpenViking 见 https://github.com/volcengine/OpenViking 。
