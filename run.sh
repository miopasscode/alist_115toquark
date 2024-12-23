#!/bin/bash

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 切换到项目目录
cd $DIR

# 检查日志目录
mkdir -p logs
mkdir -p cache/file_lists

# 检查是否已经在运行
if [ -f .pid ]; then
    PID=$(cat .pid)
    if ps -p $PID > /dev/null; then
        echo "程序已经在运行中 (PID: $PID)"
        exit 1
    else
        rm .pid
    fi
fi

# 获取当前日期
DATE=$(date +%Y%m%d)

# 启动程序并将输出重定向到日志文件
nohup python3 main.py > logs/console_${DATE}.log 2>&1 &

# 保存进程ID
echo $! > .pid

echo "程序已在后台启动，进程ID: $!"
echo "查看日志: tail -f logs/console_${DATE}.log" 