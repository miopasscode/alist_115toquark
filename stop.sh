#!/bin/bash

if [ -f .pid ]; then
    PID=$(cat .pid)
    if ps -p $PID > /dev/null; then
        echo "正在停止进程 $PID..."
        # 先发送 SIGTERM 信号
        kill -15 $PID
        
        # 等待进程结束
        COUNTER=0
        while ps -p $PID > /dev/null && [ $COUNTER -lt 10 ]; do
            sleep 1
            let COUNTER=COUNTER+1
        done
        
        # 如果进程还在运行，强制结束
        if ps -p $PID > /dev/null; then
            echo "进程未响应，强制终止..."
            kill -9 $PID
        fi
        
        rm .pid
        echo "程序已停止"
    else
        echo "程序未运行"
        rm .pid
    fi
else
    echo "找不到进程ID文件"
fi 