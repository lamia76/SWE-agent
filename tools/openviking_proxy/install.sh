#!/bin/bash
# OpenViking Proxy Bundle：与 tools/openviking 相同的调用方式
# 在容器内安装 OpenViking CLI（ov_*），通过本 bundle 的 ov.conf 使用 OpenViking 服务（本地向量库 + 远程 embedding 等）

set -e

echo "=========================================="
echo "OpenViking (local CLI) Installation"
echo "=========================================="
echo ""

# 脚本所在目录即 bundle 根目录（容器内为 /root/tools/openviking_proxy）
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

# 确保 pip 安装的 ov_* 或 openviking 所在目录在 PATH 中，便于后续 which 检查与调用
PYTHON_BIN=$(python3 -c "import sys; print(sys.prefix)")/bin
export PATH="$PYTHON_BIN:$PATH"
echo "✓ PATH includes $PYTHON_BIN"
echo ""

# 使用本 bundle 的配置文件（与 tools/openviking 一致：本地 CLI 读 ov.conf）
CONF_FILE="${bundle_dir}/ov.conf.third_party_api"
if [ -f "${bundle_dir}/ov.conf" ]; then
    CONF_FILE="${bundle_dir}/ov.conf"
fi
if [ -f "$CONF_FILE" ]; then
    export OPENVIKING_CONFIG_FILE="$CONF_FILE"
    echo "✓ OPENVIKING_CONFIG_FILE=$OPENVIKING_CONFIG_FILE"
else
    echo "⚠ Config not found: $CONF_FILE (set OPENVIKING_CONFIG_FILE manually)"
fi

export OPENVIKING_DATA_DIR="${OPENVIKING_DATA_DIR:-./.openviking}"
if [ ! -d "$OPENVIKING_DATA_DIR" ]; then
    mkdir -p "$OPENVIKING_DATA_DIR"
    echo "✓ Created OPENVIKING_DATA_DIR=$OPENVIKING_DATA_DIR"
else
    echo "✓ OPENVIKING_DATA_DIR=$OPENVIKING_DATA_DIR"
fi
echo ""

echo "=========================================="
echo "Installation Complete"
echo "=========================================="
echo "OpenViking tools (same as tools/openviking):"
echo "  - ov_index_repo  - Index repository"
echo "  - ov_wait        - Wait for processing"
echo "  - ov_find        - Semantic search"
echo "  - ov_abstract    - Brief summary (L0)"
echo "  - ov_overview    - Structured overview (L1)"
echo "  - ov_read        - Full content (L2)"
echo "  - ov_ls          - List directory"
echo "  - ov_glob        - Find by pattern"
echo ""
echo "Quick start:"
echo "  1. ov_index_repo .     # e.g. in /testbed"
echo "  2. ov_wait"
echo "  3. ov_find \"your query\""
echo ""
