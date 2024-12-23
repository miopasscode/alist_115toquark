# AList 115到夸克网盘同步工具

一个基于 AList 的自动化工具，用于将 115 网盘文件智能同步到夸克网盘。

## ✨ 特性

- 🔄 自动同步
  - 定时检测新文件
  - 增量同步更新
  - 智能断点续传
- 🛠 智能处理
  - 自动处理特殊字符
  - 文件名兼容性检查
  - 重复文件检测
- 📊 任务管理
  - 多任务并发处理
  - 失败自动重试
  - 状态实时监控
- 🌐 可视化界面
  - 实时进度展示
  - 任务状态查看
  - 手动操作支持

## 🚀 快速开始

### 环境要求

- Python 3.8+
- AList 服务器（已配置 115 和夸克网盘）
- Linux/Windows 系统

### 安装步骤

<<<<<<< HEAD
1. 克隆项目
```bash
git clone https://github.com/miopasscode/alist_115toquark.git
cd alist_115toquark
```

2. 运行部署脚本
```bash
bash deploy.sh
```

部署脚本会自动：
- 安装 Python 依赖
- 创建必要的目录
- 生成配置文件
- 创建管理脚本
- 询问是否安装为系统服务(开机自启)

### 配置文件修改

使用文本编辑器修改配置文件：
```bash
# 使用 nano 编辑器（推荐新手使用）
nano config/config.json

# 或者使用 vim 编辑器
vim config/config.json
```

需要修改的主要配置项：
```json
{
    "alist": {
        "host": "localhost",     // 改为您的 AList 服务器地址
        "port": 5244,           // AList 端口，一般不需要修改
        "username": "admin",    // 改为您的 AList 用户名
        "password": "123456"    // 改为您的 AList 密码
    },
    "sync": {
        "source": "/115",      // 改为您的 115 网盘目录
        "target": "/quark"     // 改为您的夸克网盘目录
    }
}
```

### 服务管理

根据部署时的选择，有两种管理方式：

系统服务方式：
```bash
# 启动服务
sudo systemctl start alist-sync

# 停止服务
sudo systemctl stop alist-sync

# 重启服务
sudo systemctl restart alist-sync

# 查看状态
sudo systemctl status alist-sync

# 查看日志
journalctl -u alist-sync -f
```

普通方式：
```bash
# 启动服务
bash scripts/run.sh

# 停止服务
bash scripts/stop.sh

# 查看日志
tail -f logs/app.log
```
=======
- - + 方式一：普通启动
  1. 克隆项目
  ```bash
  git clone https://github.com/miopasscode/alist_115toquark.git
  cd alist_115toquark
  ```
  
  2. 安装依赖
  ```bash
  pip3 install -r requirements.txt
  ```
  
  3. 修改配置文件
  ```bash
  cp config/config.example.json config/config.json
  # 编辑 config/config.json 修改配置
  ```
  
  4. 启动服务
  ```bash
  bash scripts/run.sh
  ```
 
 方式二：系统服务（推荐）
 1. 克隆项目
 ```bash
 git clone https://github.com/miopasscode/alist_115toquark.git
 cd alist_115toquark
 ```
 
 2. 运行部署脚本
 ```bash
 bash deploy.sh
 ```
 
 部署脚本会自动：
 - 安装 Python 依赖
 - 创建必要的目录
 - 生成配置文件
 - 创建管理脚本
 - 询问是否安装为系统服务(开机自启)
  
  ### 服务管理
  
  根据部署时的选择，有两种管理方式：
  
  系统服务方式：
  ```bash
  # 启动服务
  sudo systemctl start alist-sync
  
  # 停止服务
  sudo systemctl stop alist-sync
  
  # 重启服务
  sudo systemctl restart alist-sync
  
  # 查看状态
  sudo systemctl status alist-sync
  
  # 查看日志
  journalctl -u alist-sync -f
  ```
  
  普通方式：
  ```bash
  # 启动服务
  bash scripts/run.sh
  
  # 停止服务
  bash scripts/stop.sh
  
  # 查看日志
  tail -f logs/app.log
  ```
>>>>>>> e705c75 (Update README.md)

## 📖 使用指南

### Web 控制台

访问 `http://your-ip:62333` 进入控制台：

- 查看同步任务状态
- 手动触发同步
- 查看运行日志
- 管理任务队列

### 命令行工具

```bash
# 查看状态
bash scripts/status.sh

# 停止服务
bash scripts/stop.sh

# 查看日志
tail -f logs/app.log
```

## 📁 项目结构

```
├── main.py           # 主程序
├── requirements.txt  # 依赖清单
├── src/             # 源代码
│   ├── api/         # API 接口
│   ├── utils/       # 工具函数
│   └── web/         # Web 服务
├── config/          # 配置文件
├── logs/            # 日志目录
└── scripts/         # 运维脚本
```

## 🔧 配置说明

### 核心配置项

```json
{
    "alist": {
        "host": "localhost",     // AList 服务器地址
        "port": 5244,           // AList 服务器端口
        "username": "admin",    // AList 管理员用户名
        "password": "123456",   // AList 管理员密码
        "use_https": false      // 是否使用 HTTPS
    },
    "sync": {
        "source": "/115",           // 115网盘根目录
        "target": "/quark",         // 夸克网盘根目录
        "exclude": [                // 排除的目录和文件
            "tmp",
            "*.tmp"
        ],
        "interval": 3600,          // 同步间隔(秒)
        "concurrent": 3,           // 并发任务数
        "retry_times": 3,          // 失败重试次数
        "retry_interval": 300      // 重试间隔(秒)
    },
    "web": {
        "host": "0.0.0.0",         // Web服务监听地址
        "port": 62333,             // Web服务端口
        "secret_key": "your-key"   // Web服务密钥
    },
    "log": {
        "level": "INFO",           // 日志级别
        "file": "logs/app.log",    // 日志文件路径
        "max_size": 10,            // 单个日志文件大小(MB)
        "backup_count": 5          // 保留的日志文件数
    }
}
```

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| alist.host | AList 服务地址 | localhost |
| alist.port | AList 服务端口 | 5244 |
| alist.username | AList 用户名 | admin |
| alist.password | AList 密码 | - |
| alist.use_https | 使用HTTPS | false |
| sync.source | 115网盘目录 | /115 |
| sync.target | 夸克网盘目录 | /quark |
| sync.exclude | 排除的文件 | [] |
| sync.interval | 同步间隔(秒) | 3600 |
| sync.concurrent | 并发任务数 | 3 |
| sync.retry_times | 重试次数 | 3 |
| sync.retry_interval | 重试间隔(秒) | 300 |
| web.host | Web监听地址 | 0.0.0.0 |
| web.port | Web界面端口 | 62333 |
| web.secret_key | Web密钥 | - |
| log.level | 日志级别 | INFO |
| log.file | 日志文件 | logs/app.log |
| log.max_size | 日志大小(MB) | 10 |
| log.backup_count | 日志文件数 | 5 |

## 🚨 常见问题

### 1. 同步失败
- 检查网络连接
- 验证 AList 配置
- 查看错误日志

### 2. 文件名问题
- 确认源文件存在
- 检查特殊字符
- 验证权限设置

