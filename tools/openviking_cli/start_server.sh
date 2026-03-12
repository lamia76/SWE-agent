#!/usr/bin/env bash
# 使用 tools/openviking/ov.conf 启动 OpenViking Server，与 tools/openviking 使用同一套模型与接口（embedding/vlm/rerank）
# 需在已安装 openviking 且能执行 openviking-server 的环境运行；通常在与 embedding/vlm 同一台机（如 141.61.16.3）上执行

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 默认使用 tools/openviking/ov.conf，保证 openviking_cli 与 tools/openviking 用同一模型、同一接口
OV_CONF_DEFAULT="$(cd "$SCRIPT_DIR/../openviking" && pwd)/ov.conf"
OV_CONF="${1:-$OV_CONF_DEFAULT}"

if [ ! -f "$OV_CONF" ]; then
    echo "错误: 配置文件不存在: $OV_CONF"
    echo "建议: 使用 tools/openviking/ov.conf，即 ./start_server.sh $OV_CONF_DEFAULT"
    exit 1
fi

export OPENVIKING_CONFIG_FILE="$OV_CONF"
echo "使用配置: $OV_CONF (与 tools/openviking 同一套模型与接口)"
echo "启动 OpenViking Server..."
exec openviking-server --config "$OV_CONF"
