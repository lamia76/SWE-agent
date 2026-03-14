#!/bin/bash
# OpenViking CLI Bundle：通过 ov 命令连接 OpenViking Server（HTTP）
# 模型已在他处部署，配置 ovcli.conf 的 url 即可直接调用

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

CLI_CONF="${bundle_dir}/ovcli.conf"
if [ -f "$CLI_CONF" ]; then
    export OPENVIKING_CLI_CONFIG_FILE="$CLI_CONF"
    echo "✓ OPENVIKING_CLI_CONFIG_FILE=$CLI_CONF"
else
    echo "⚠ ovcli.conf not found: $CLI_CONF (set OPENVIKING_CLI_CONFIG_FILE or OPENVIKING_SERVER_URL)"
fi
echo ""

CA_BUNDLE="${bundle_dir}/tls-ca-bundle.pem"
if [ -f "$CA_BUNDLE" ]; then
    CA_ABS=$(cd "$(dirname "$CA_BUNDLE")" && pwd)/$(basename "$CA_BUNDLE")
    export REQUESTS_CA_BUNDLE="$CA_ABS"
    export SSL_CERT_FILE="$CA_ABS"
    echo "✓ TLS certificate: $CA_ABS"
fi
echo ""

PYTHON_BIN=$(python3 -c "import sys; print(sys.prefix)")/bin
BUNDLE_BIN="$bundle_dir/bin"
export PATH="$BUNDLE_BIN:$PYTHON_BIN:$PATH"
echo "✓ PATH includes $BUNDLE_BIN and $PYTHON_BIN"
echo ""

echo "=========================================="
echo "Installation Complete"
echo "=========================================="
echo "OpenViking CLI tools (connect to Server via ov):"
echo "  - ov_index_repo  - ov add-resource"
echo "  - ov_wait        - ov system wait"
echo "  - ov_find        - ov find"
echo "  - ov_abstract    - ov abstract"
echo "  - ov_overview    - ov overview"
echo "  - ov_read        - ov read"
echo "  - ov_ls          - ov ls"
echo "  - ov_glob        - ov glob"
echo ""
echo "Edit ovcli.conf to set url (OpenViking Server) and api_key."
echo ""
