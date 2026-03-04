#!/bin/bash
# OpenViking Proxy Bundle 安装脚本（主机侧）
# 与 tools/openviking 的安装方式对齐：检查环境、安装依赖、设置配置文件路径。
# 主机上运行此脚本后，可启动 proxy_server.py，供 SWE-agent 容器通过 HTTP 调用 OpenViking。

set -e

echo "=========================================="
echo "OpenViking Proxy Bundle (Host) Installation"
echo "=========================================="
echo ""

# 解析脚本所在目录（bundle 根目录）
bundle_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
cd "$bundle_dir"

# 检查 Python
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "Error: python3 or python not found. Please install Python 3.8+."
    exit 1
fi
PYTHON=${PYTHON:-$(command -v python3 2>/dev/null || command -v python)}
echo "✓ Python: $($PYTHON --version 2>/dev/null || true)"

# 检查 pip
if ! $PYTHON -m pip --version &>/dev/null; then
    echo "Error: pip not found. Please install pip."
    exit 1
fi
echo "✓ pip available"
echo ""

# 安装 OpenViking SDK（Proxy 依赖 VikingClient，VikingClient 依赖 openviking）
echo "Installing OpenViking SDK..."
if $PYTHON -m pip install --upgrade openviking; then
    echo "✓ OpenViking SDK installed"
else
    echo "✗ Failed to install OpenViking SDK"
    exit 1
fi
echo ""

# VikingClient 来自 OpenViking/bot（vikingbot），二选一：
# 1) 将 OpenViking/bot 加入 PYTHONPATH（需先有 OpenViking 源码）
# 2) 在 OpenViking/bot 目录执行 pip install -e .
echo "VikingClient (for proxy_server.py) is provided by OpenViking/bot:"
echo "  Option A: export PYTHONPATH=\"/path/to/OpenViking/bot:\$PYTHONPATH\""
echo "  Option B: cd /path/to/OpenViking/bot && pip install -e ."
echo ""

# 配置文件：使用本 bundle 内的示例配置
CONF_FILE="${bundle_dir}/ov.conf.third_party_api"
if [ -f "$CONF_FILE" ]; then
    export OPENVIKING_CONFIG_FILE="$CONF_FILE"
    echo "✓ Config file set: OPENVIKING_CONFIG_FILE=$OPENVIKING_CONFIG_FILE"
else
    echo "⚠ Config file not found: $CONF_FILE (set OPENVIKING_CONFIG_FILE manually)"
fi
echo ""

# VikingClient 会读取 ~/.vikingbot/config.json
VIKINGBOT_DIR="$HOME/.vikingbot"
if [ ! -d "$VIKINGBOT_DIR" ]; then
    mkdir -p "$VIKINGBOT_DIR"
    echo "✓ Created directory: $VIKINGBOT_DIR (you may add config.json for VikingClient)"
else
    echo "✓ Directory exists: $VIKINGBOT_DIR"
fi
echo ""

echo "=========================================="
echo "Installation Complete (Host)"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Ensure VikingClient is available (PYTHONPATH to OpenViking/bot or pip install -e . in bot)"
echo "  2. Index target repo: openviking add-resource <path-or-url> --wait"
echo "  3. Start proxy: cd $bundle_dir && python proxy_server.py [--port 8765]"
echo "  4. In SWE-agent run env, set OPENVIKING_PROXY_URL=http://host.docker.internal:8765 (or host IP)"
echo ""
