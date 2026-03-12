#!/usr/bin/env bash
# 使用与 tools/openviking 一致的 ov.conf 启动 OpenViking Server（模型本地部署，url/api_key 与 ov.conf 一致）
# 需在已安装 openviking 且能执行 openviking-server 的环境运行；通常在与 embedding/vlm 同一台机（如 141.61.16.3）上执行

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OV_CONF="${1:-$SCRIPT_DIR/ov.conf}"

if [ ! -f "$OV_CONF" ]; then
    echo "错误: 配置文件不存在: $OV_CONF"
    exit 1
fi

export OPENVIKING_CONFIG_FILE="$OV_CONF"
echo "使用配置: $OV_CONF (与 tools/openviking/ov.conf 的模型 url/api_key 一致)"
echo "启动 OpenViking Server..."
exec openviking-server --config "$OV_CONF"
