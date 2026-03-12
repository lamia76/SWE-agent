# 使用第三方 API 及自定义 TLS 证书（CLI 方式）

当 OpenViking Server 使用 HTTPS 或自签名/私有 CA 证书时，可通过本说明配置证书。逻辑与 `tools/openviking` 保持一致。

## 1. 配置文件（ovcli.conf）

本 bundle 使用 **ovcli.conf** 连接 OpenViking Server（与 `tools/openviking` 的 ov.conf 对应：后者为嵌入式本地配置，本处为 CLI 连 Server 配置）。

- 默认路径：本 bundle 内 `ovcli.conf`
- 环境变量：`OPENVIKING_CLI_CONFIG_FILE` 指向任意 ovcli.conf 路径

默认与 tools/openviking 一致，为同一部署地址（如 `http://141.61.16.3:1933`）。若使用 HTTPS 或自建域名可改为：

```json
{
  "url": "https://your-openviking-server.example.com",
  "api_key": "your-api-key",
  "agent_id": null,
  "timeout": 120.0,
  "output": "table"
}
```

## 2. 使用 tls-ca-bundle.pem

若 Server 为 HTTPS 且使用自签名或私有 CA，将 `tls-ca-bundle.pem` 放在本 bundle 目录下，install 及 bin 脚本会自动设置：

- `REQUESTS_CA_BUNDLE`
- `SSL_CERT_FILE`

也可在**运行 SWE-agent 或任意 ov 命令前**手动设置：

### Linux / macOS

```bash
export REQUESTS_CA_BUNDLE=/path/to/tools/openviking_cli/tls-ca-bundle.pem
export SSL_CERT_FILE=/path/to/tools/openviking_cli/tls-ca-bundle.pem
export OPENVIKING_CLI_CONFIG_FILE=/path/to/tools/openviking_cli/ovcli.conf
# 然后运行 agent 或 ov 命令
ov find "your query"
```

### Windows PowerShell

```powershell
$env:REQUESTS_CA_BUNDLE = "C:\path\to\tools\openviking_cli\tls-ca-bundle.pem"
$env:SSL_CERT_FILE = "C:\path\to\tools\openviking_cli\tls-ca-bundle.pem"
$env:OPENVIKING_CLI_CONFIG_FILE = "C:\path\to\tools\openviking_cli\ovcli.conf"
```

## 3. 快速启动脚本

```bash
cd SWE-agent/tools/openviking_cli
chmod +x run_with_ssl.sh

# 使用默认路径（本目录 ovcli.conf + tls-ca-bundle.pem），执行后续命令
./run_with_ssl.sh ov find "your query"
./run_with_ssl.sh ov add-resource . --wait
```

或指定路径：

```bash
./run_with_ssl.sh /path/to/ovcli.conf /path/to/tls-ca-bundle.pem ov find "query"
```

## 4. 注意事项

- Server 为 **HTTP**（如 `http://localhost:1933`）时无需证书。
- Server 为 **HTTPS** 且为公网 CA 签发时，通常无需额外配置。
- 仅当 Server 或其后端 API 使用自签名/私有 CA 时，需配置 `tls-ca-bundle.pem` 与上述环境变量。
