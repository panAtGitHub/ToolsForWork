#!/usr/bin/env bash
# start_tools.command — 双击即可启动后端服务

# 切到脚本所在目录（ToolsForWork）
cd "$(dirname "$0")"

# 激活 Python 虚拟环境
source venv/bin/activate

# 进入后端目录并启动 Flask
cd backend
python app.py
