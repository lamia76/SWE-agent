#!/usr/bin/env bash
# 使用自定义 TLS 证书和第三方 API 配置启动 OpenViking Proxy
# 用法: ./run_with_ssl.sh [ov.conf路径] [tls-ca-bundle.pem路径]
# 启动前请设置: export PYTHONPATH="/path/to/OpenViking/bot:$PYTHONPATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OV_CONF="${1:-$SCRIPT_DIR/ov.conf.third_party_api}"
CA_BUNDLE="${2:-$SCRIPT_DIR/tls-ca-bundle.pem}"

if [ ! -f "$OV_CONF" ]; then
    echo "错误: 配置文件不存在: $OV_CONF"
    exit 1
fi

if [ -f "$CA_BUNDLE" ]; then
    export REQUESTS_CA_BUNDLE="$CA_BUNDLE"
    export SSL_CERT_FILE="$CA_BUNDLE"
    echo "已设置 TLS 证书: $CA_BUNDLE"
else
    echo "警告: 未找到 tls-ca-bundle.pem ($CA_BUNDLE)，使用系统默认证书"
fi

export OPENVIKING_CONFIG_FILE="$OV_CONF"
echo "使用配置: $OV_CONF"
echo ""
echo "启动 OpenViking Proxy..."
exec python "$SCRIPT_DIR/proxy_server.py" --port 8765
