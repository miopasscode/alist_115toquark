#!/bin/bash

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

# 检查更新文件是否存在
if [ ! -f "update.zip" ]; then
    echo "错误: 未找到更新文件 (update.zip)"
    exit 1
fi

# 停止当前运行的程序
if [ -f .pid ]; then
    echo "停止当前运行的程序..."
    ./stop.sh
fi

# 备份当前代码
echo "备份当前代码..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp -r src config main.py requirements.txt $BACKUP_DIR/

# 解压更新文件
echo "解压更新文件..."
unzip -o update.zip

# 设置权限
echo "设置权限..."
chmod +x run.sh stop.sh status.sh update.sh
chmod 755 logs cache cache/file_lists

# 删除更新文件
echo "清理更新文件..."
rm update.zip

# 重启程序
echo "重启程序..."
./run.sh

# 查看状态
echo "程序状态:"
./status.sh 