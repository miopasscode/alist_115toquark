#!/bin/bash

# 获取当前目录的绝对路径
WORK_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

# 创建系统服务配置文件
sudo tee /etc/systemd/system/alist-sync.service << EOF
[Unit]
Description=AList 115 to Quark Sync Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
ExecStart=/usr/bin/python3 $WORK_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重载系统服务配置
sudo systemctl daemon-reload

# 启用服务开机自启
sudo systemctl enable alist-sync

echo "系统服务安装完成！"
echo "使用以下命令管理服务："
echo "启动服务：sudo systemctl start alist-sync"
echo "停止服务：sudo systemctl stop alist-sync"
echo "查看状态：sudo systemctl status alist-sync"
echo "查看日志：journalctl -u alist-sync -f" 