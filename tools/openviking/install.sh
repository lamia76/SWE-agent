#!/bin/bash
# OpenViking Tool Bundle Installation Script for SWE-agent

set -e  # Exit on any error

echo "=========================================="
echo "OpenViking Tool Bundle Installation"
echo "=========================================="
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo "✓ Python 3 found: $(which python)"

# Check pip installation
if ! command -v pip &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo "Error: pip is not installed"
    echo "Please install pip first"
    exit 1
fi

echo "✓ pip found"
echo ""

# check go installation
if ! command version go &> /dev/null; then
    # wget https://go.dev/dl/go1.25.1.linux-arm64.tar.gz
    # wget --no-check-certificate https://mirrors.aliyun.com/golang/go1.25.1.linux-arm64.tar.gz
    curl -ko./go1.25.1.linux-arm64.tar.gz https://mirrors.aliyun.com/golang/go1.25.1.linux-arm64.tar.gz
    rm -rf /usr/local/go && tar -C /usr/local -xzf go1.25.1.linux-arm64.tar.gz
    export PATH=$PATH:/usr/local/go/bin
    export GO111MODULE=on
    export GOPROXY=https://goproxy.cn,direct
    export GOSUMDB=off
    export CA_BUNDLE_PATH=$(realpath ./tls-ca-bundle.pem)
    export SSL_CERT_FILE=$CA_BUNDLE_PATH
    # export GOINSECURE=goproxy.cn,github.com,gopkg.in
fi

# Install OpenViking SDK
echo "Installing OpenViking SDK..."
pip install --upgrade openviking
# || python -m pip install --upgrade openviking

if [ $? -eq 0 ]; then
    echo "✓ OpenViking SDK installed successfully"
else
    echo "✗ Failed to install OpenViking SDK"
    exit 1
fi

conda install -c conda-forge libstdcxx-ng=14 -y
echo ""

# Check for optional dependencies
echo "Checking optional dependencies..."

# Check for openEuler/ARM compatibility (sqlite-vec)
if python3 -c "import sqlite3" &> /dev/null; then
    echo "✓ sqlite3 available"
else
    echo "⚠ sqlite3 not available (some features may require manual setup)"
fi

echo ""

# Create data directory (optional)
echo "Creating default data directory..."
export OPENVIKING_DATA_DIR="${OPENVIKING_DATA_DIR:-./.openviking}"

if [ ! -d "$OPENVIKING_DATA_DIR" ]; then
    mkdir -p "$OPENVIKING_DATA_DIR"
    echo "✓ Created data directory: $OPENVIKING_DATA_DIR"
else
    echo "✓ Data directory already exists: $OPENVIKING_DATA_DIR"
fi

export OPENVIKING_CONFIG_FILE=$(realpath ./ov.conf)
echo "✓ Ser config file: $OPENVIKING_CONFIG_FILE"

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "OpenViking tools are now available:"
echo "  - ov_index_repo: Index a repository"
echo "  - ov_wait: Wait for processing to complete"
echo "  - ov_find: Semantic search for files"
echo "  - ov_abstract: Get brief summary (L0)"
echo "  - ov_overview: Get structured overview (L1)"
echo "  - ov_read: Read full content (L2)"
echo "  - ov_ls: List directory contents"
echo "  - ov_glob: Find files by pattern"
echo ""
echo "Quick start:"
echo "  1. ov_index_repo .            # Index current directory"
echo "  2. ov_wait                   # Wait for processing"
echo "  3. ov_find \"your query\"      # Search for files"
echo ""

