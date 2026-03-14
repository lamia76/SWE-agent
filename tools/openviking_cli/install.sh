#!/bin/bash
# OpenViking CLI Bundle：通过 ov 命令调用已部署的 OpenViking 服务
# 模型已在他处部署，仅需配置 ovcli.conf 的 url 即可直接调用

set -e

echo "=========================================="
echo "OpenViking CLI Installation"
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

# 仅使用本目录下的 ovcli.conf 作为 API 连接配置（不跨目录）
CLI_CONF="${bundle_dir}/ovcli.conf"
if [ -f "$CLI_CONF" ]; then
    export OPENVIKING_CLI_CONFIG_FILE="$CLI_CONF"
    echo "✓ OPENVIKING_CLI_CONFIG_FILE=$CLI_CONF"
else
    echo "⚠ ovcli.conf not found: $CLI_CONF (set OPENVIKING_CLI_CONFIG_FILE manually)"
fi
echo ""

# RUN_WITH_SSL_CERT 逻辑合并：证书放在本目录下 tls-ca-bundle.pem，install 自动设置（HTTPS/自签名/私有 CA 时使用）
CA_BUNDLE="${bundle_dir}/tls-ca-bundle.pem"
if [ -f "$CA_BUNDLE" ]; then
    CA_ABS=$(cd "$(dirname "$CA_BUNDLE")" && pwd)/$(basename "$CA_BUNDLE")
    export REQUESTS_CA_BUNDLE="$CA_ABS"
    export SSL_CERT_FILE="$CA_ABS"
    echo "✓ TLS certificate (from same dir): $CA_ABS"
else
    echo "ℹ No tls-ca-bundle.pem in this dir (optional; put cert here and re-run install if needed for HTTPS/custom CA)"
fi
echo ""

# 确保 ov 命令和本 bundle 的 bin 在 PATH 中
PYTHON_BIN=$(python3 -c "import sys; print(sys.prefix)")/bin
BUNDLE_BIN="$bundle_dir/bin"
export PATH="$BUNDLE_BIN:$PYTHON_BIN:$PATH"
echo "✓ PATH includes $BUNDLE_BIN and $PYTHON_BIN"
echo ""

echo "=========================================="
echo "Installation Complete"
echo "=========================================="
echo "OpenViking CLI tools:"
echo "  - ov_index_repo  - ov add-resource (index repo)"
echo "  - ov_wait        - ov system wait"
echo "  - ov_find        - ov find (semantic search)"
echo "  - ov_abstract    - ov abstract (L0)"
echo "  - ov_overview    - ov overview (L1)"
echo "  - ov_read        - ov read (L2)"
echo "  - ov_ls          - ov ls"
echo "  - ov_glob        - ov glob"
echo ""
echo "Edit ovcli.conf to set url (deployed OpenViking service) and api_key."
echo ""
