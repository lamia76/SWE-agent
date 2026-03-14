#!/bin/bash
# OpenViking 嵌入式模式：与 tools/openviking 相同逻辑，使用 SyncOpenViking SDK 本地调用
# 配置 ov.conf 中的 embedding/vlm/rerank API 地址即可，无需启动 Server

set -e

echo "=========================================="
echo "OpenViking (Embedded) Installation"
echo "=========================================="
echo ""

bundle_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
cd "$bundle_dir"

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "Error: python3 or python not found. Please install Python 3.8+."
    exit 1
fi
echo "✓ Python: $(python3 --version 2>/dev/null || python --version 2>/dev/null)"

if ! python3 -m pip --version &>/dev/null; then
    echo "Error: pip not found."
    exit 1
fi
echo "✓ pip available"
echo ""

echo "Installing OpenViking SDK..."
pip install --upgrade openviking
if [ $? -eq 0 ]; then
    echo "✓ OpenViking SDK installed"
else
    echo "✗ Failed to install OpenViking SDK"
    exit 1
fi
echo ""

# 嵌入式模式：使用 ov.conf（与 tools/openviking 格式相同）
OV_CONF="${bundle_dir}/ov.conf"
if [ -f "$OV_CONF" ]; then
    export OPENVIKING_CONFIG_FILE="$(cd "$(dirname "$OV_CONF")" && pwd)/$(basename "$OV_CONF")"
    echo "✓ OPENVIKING_CONFIG_FILE=$OPENVIKING_CONFIG_FILE"
else
    echo "⚠ ov.conf not found: $OV_CONF (edit embedding/vlm/rerank API in ov.conf)"
fi
echo ""

# 数据目录
export OPENVIKING_DATA_DIR="${OPENVIKING_DATA_DIR:-./.openviking}"
if [ ! -d "$OPENVIKING_DATA_DIR" ]; then
    mkdir -p "$OPENVIKING_DATA_DIR"
    echo "✓ Created data directory: $OPENVIKING_DATA_DIR"
else
    echo "✓ Data directory: $OPENVIKING_DATA_DIR"
fi
echo ""

# 可选：TLS 证书（embedding/vlm 使用 HTTPS 自签名时）
CA_BUNDLE="${bundle_dir}/tls-ca-bundle.pem"
if [ -f "$CA_BUNDLE" ]; then
    CA_ABS=$(cd "$(dirname "$CA_BUNDLE")" && pwd)/$(basename "$CA_BUNDLE")
    export REQUESTS_CA_BUNDLE="$CA_ABS"
    export SSL_CERT_FILE="$CA_ABS"
    echo "✓ TLS certificate: $CA_ABS"
fi
echo ""

# PATH
PYTHON_BIN=$(python3 -c "import sys; print(sys.prefix)")/bin
BUNDLE_BIN="$bundle_dir/bin"
export PATH="$BUNDLE_BIN:$PYTHON_BIN:$PATH"
echo "✓ PATH includes $BUNDLE_BIN and $PYTHON_BIN"
echo ""

echo "=========================================="
echo "Installation Complete"
echo "=========================================="
echo "OpenViking tools (embedded mode):"
echo "  - ov_index_repo  - index repo"
echo "  - ov_wait        - wait for processing"
echo "  - ov_find        - semantic search"
echo "  - ov_abstract    - L0 abstract"
echo "  - ov_overview    - L1 overview"
echo "  - ov_read        - L2 full content"
echo "  - ov_ls          - list directory"
echo "  - ov_glob        - glob pattern"
echo ""
echo "Edit ov.conf to set embedding/vlm/rerank API addresses."
echo ""
