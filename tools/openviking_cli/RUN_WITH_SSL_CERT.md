# 证书配置说明（逻辑已合并到 install.sh）

当 OpenViking Server 或其后端 API 使用 **HTTPS 且为自签名/私有 CA** 时，需要指定 CA 证书。该逻辑已合并到 **install.sh**：将证书放在**本目录**下即可。

## 使用方式

1. 将 CA 证书文件命名为 **tls-ca-bundle.pem**，放在本 bundle 目录下（与 install.sh 同目录）。
2. 执行 **install.sh**（或若已安装过，放入证书后重新执行一次 install.sh）。install 会检测该文件并设置：
   - `REQUESTS_CA_BUNDLE`
   - `SSL_CERT_FILE`
3. 各 bin 脚本（ov_index_repo、ov_find 等）在运行时也会检测本目录下的 tls-ca-bundle.pem 并自动设置上述环境变量，无需额外操作。

## 说明

- Server 为 **HTTP**（如 `http://141.61.16.3:8090`，端口与 ov.conf `server.port` 一致）时无需证书。
- Server 为 **HTTPS** 且为公网 CA 签发时，通常无需配置。
- 仅当 Server 或其后端 API 使用**自签名/私有 CA** 时，需将对应 CA 证书放到本目录并命名为 tls-ca-bundle.pem，然后执行 install.sh。
