#!/bin/bash

check_process() {
    local PID=$1
    if ps -p $PID -o pid,ppid,user,%cpu,%mem,start,time,command > /dev/null; then
        return 0
    else
        return 1
    fi
}

if [ -f .pid ]; then
    PID=$(cat .pid)
    if check_process $PID; then
        echo "程序状态: 运行中"
        echo "进程信息:"
        ps -p $PID -o pid,ppid,user,%cpu,%mem,start,time,command
        echo -e "\n系统资源使用:"
        top -b -n 1 -p $PID | tail -n 1
        echo -e "\n最新日志:"
        tail -n 10 logs/copy_task_$(date +%Y%m%d).log
        echo -e "\n任务状态:"
        if [ -f cache/file_lists/task_status.json ]; then
            cat cache/file_lists/task_status.json
        else
            echo "未找到任务状态文件"
        fi
    else
        echo "程序未运行"
        rm .pid
    fi
else
    echo "程序未运行"
fi 