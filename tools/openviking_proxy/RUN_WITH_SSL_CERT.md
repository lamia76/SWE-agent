# 使用第三方 API 及自定义 TLS 证书

当 embedding、vlm、rerank 等 OpenViking 后端 API 使用自签名或私有 CA 证书时，需要指定证书路径。

## 1. 配置文件

将 `ov.conf.third_party_api` 复制为 OpenViking 使用的 ov.conf，或通过环境变量指定：

```bash
# 使用本 bundle 内的示例配置
export OPENVIKING_CONFIG_FILE=/path/to/SWE-agent/tools/openviking_proxy/ov.conf.third_party_api

# 或复制到 OpenViking 默认位置
cp SWE-agent/tools/openviking_proxy/ov.conf.third_party_api ~/.openviking/ov.conf
```

## 2. 使用 tls-ca-bundle.pem

若目录下存在 `tls-ca-bundle.pem`，在**启动 proxy_server 之前**设置环境变量：

### Linux / macOS

```bash
# 推荐：同时设置两个
export REQUESTS_CA_BUNDLE=/path/to/tls-ca-bundle.pem
export SSL_CERT_FILE=/path/to/tls-ca-bundle.pem

# 启动 proxy
export PYTHONPATH="/path/to/OpenViking/bot:$PYTHONPATH"
python SWE-agent/tools/openviking_proxy/proxy_server.py --port 8765
```

### Windows PowerShell

```powershell
$env:REQUESTS_CA_BUNDLE = "C:\path\to\tls-ca-bundle.pem"
$env:SSL_CERT_FILE = "C:\path\to\tls-ca-bundle.pem"
python SWE-agent/tools/openviking_proxy/proxy_server.py
```

### 证书与本 bundle 同目录

将 `tls-ca-bundle.pem` 放在 `tools/openviking_proxy/` 下，使用 `run_with_ssl.sh` 启动。

## 3. 快速启动脚本

```bash
cd SWE-agent/tools/openviking_proxy
chmod +x run_with_ssl.sh

# 使用默认路径（本目录下的 ov.conf.third_party_api 和 tls-ca-bundle.pem）
./run_with_ssl.sh

# 或指定路径
./run_with_ssl.sh /path/to/ov.conf /path/to/tls-ca-bundle.pem
```

## 4. 注意事项

- `141.61.16.3` 使用 **HTTP**，无需证书；`api-vikingdb.vikingdb.cn-beijing.volces.com` 使用 **HTTPS**，需要证书
- 若 rerank 的 `ak`/`sk` 为 `null`，rerank 不可用，search 仅用向量相似度
- 若 embedding API 是 **OpenAI 兼容**，将 `embedding.dense.provider` 改为 `"openai"`
