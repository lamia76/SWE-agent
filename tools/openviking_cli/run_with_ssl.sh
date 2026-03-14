#!/usr/bin/env bash
# 使用自定义 TLS 证书和 ovcli.conf 执行 ov 命令（CLI 连 Server）
# 用法: ./run_with_ssl.sh [ovcli.conf路径] [tls-ca-bundle.pem路径] <ov 命令及参数...>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OVCLI_CONF="$SCRIPT_DIR/ovcli.conf"
CA_BUNDLE="$SCRIPT_DIR/tls-ca-bundle.pem"
if [ -n "$1" ] && [ -f "$1" ]; then
    OVCLI_CONF="$1"
    shift
    if [ -n "$1" ] && [ -f "$1" ]; then
        CA_BUNDLE="$1"
        shift
    fi
fi

if [ ! -f "$OVCLI_CONF" ]; then
    echo "错误: 配置文件不存在: $OVCLI_CONF"
    exit 1
fi

export OPENVIKING_CLI_CONFIG_FILE="$OVCLI_CONF"
echo "使用配置: $OVCLI_CONF"

if [ -f "$CA_BUNDLE" ]; then
    export REQUESTS_CA_BUNDLE="$CA_BUNDLE"
    export SSL_CERT_FILE="$CA_BUNDLE"
    echo "已设置 TLS 证书: $CA_BUNDLE"
fi

if [ $# -eq 0 ]; then
    echo "未传入 ov 命令，仅已导出环境变量。"
    exit 0
fi

exec "$@"
