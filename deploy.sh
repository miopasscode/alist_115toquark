#!/bin/bash

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "请先安装 Python 3"
    exit 1
fi

# 创建必要的目录
mkdir -p config
mkdir -p logs
mkdir -p cache/file_lists
mkdir -p scripts

# 创建配置文件
if [ ! -f config/config.example.json ]; then
    cat > config/config.example.json << 'EOF'
{
    "alist": {
        "host": "localhost",
        "port": 5244,
        "username": "admin",
        "password": "your-password",
        "use_https": false
    },
    "sync": {
        "source": "/115",
        "target": "/quark",
        "exclude": [
            "tmp",
            "*.tmp"
        ],
        "interval": 3600,
        "concurrent": 3,
        "retry_times": 3,
        "retry_interval": 300
    },
    "web": {
        "host": "0.0.0.0",
        "port": 62333,
        "secret_key": "your-key"
    },
    "log": {
        "level": "INFO",
        "file": "logs/app.log",
        "max_size": 10,
        "backup_count": 5
    }
}
EOF
fi

# 复制配置文件
if [ ! -f config/config.json ]; then
    cp config/config.example.json config/config.json
    echo "请使用以下命令修改配置文件："
    echo "nano config/config.json  # 如果使用 nano 编辑器"
    echo "vim config/config.json   # 如果使用 vim 编辑器"
    echo ""
    echo "配置文件说明："
    echo "- alist.host: AList 服务器地址"
    echo "- alist.port: AList 服务器端口(默认5244)"
    echo "- alist.username: AList 用户名"
    echo "- alist.password: AList 密码"
    echo "- sync.source: 115网盘目录"
    echo "- sync.target: 夸克网盘目录"
    echo ""
    echo "修改完成后继续..."
    read -p "按回车键继续..."
fi

# 安装依赖
pip3 install -r requirements.txt

# 创建启动脚本
cat > scripts/run.sh << 'EOF'
#!/bin/bash
python3 main.py
EOF

# 创建停止脚本
cat > scripts/stop.sh << 'EOF'
#!/bin/bash
pkill -f "python3 main.py"
EOF

# 创建状态检查脚本
cat > scripts/status.sh << 'EOF'
#!/bin/bash
if pgrep -f "python3 main.py" > /dev/null; then
    echo "服务正在运行"
else
    echo "服务未运行"
fi
EOF

# 赋予脚本执行权限
chmod +x scripts/*.sh

# 询问是否安装系统服务
read -p "是否安装为系统服务(开机自启)? [y/N] " install_service
if [[ $install_service =~ ^[Yy]$ ]]; then
    bash scripts/install_service.sh
fi

echo "部署完成!"
if [[ ! $install_service =~ ^[Yy]$ ]]; then
    echo "请修改配置文件后运行: bash scripts/run.sh"
else
    echo "请修改配置文件后运行: sudo systemctl start alist-sync"
fi